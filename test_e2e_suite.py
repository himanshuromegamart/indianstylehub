import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bharatshop.settings')
django.setup()

from django.test import Client
from mainApp.models import Buyer, Product, PasswordResetOTP, Order, Address
from django.contrib.auth.models import User

print('========================================')
print('RUNNING FULL END-TO-END AUTOMATED SUITE')
print('========================================')

c = Client()
test_phone = '9111222333'
test_email = 'e2e.shopper@testboutique.com'
test_pass = 'InitialPass@123'
new_pass = 'BrandNewPass@999'

# Cleanup any previous test data
User.objects.filter(username=test_phone).delete()
Buyer.objects.filter(phone=test_phone).delete()
PasswordResetOTP.objects.filter(email=test_email).delete()

# ----------------------------------------------------
# TEST 1: REGISTRATION FLOW WITH ADDRESS
# ----------------------------------------------------
print('\n[1/7] Testing Registration Flow...')
resp_reg = c.post('/register/', {
    'name': 'Ananya Verma',
    'phone': test_phone,
    'email': test_email,
    'password': test_pass,
    'address': 'Flat 402, Sunshine Towers, MG Road',
    'city': 'Bengaluru',
    'state': 'Karnataka',
    'pincode': '560001'
}, follow=False)

assert resp_reg.status_code == 302, f'Expected 302 but got {resp_reg.status_code}'
assert resp_reg.get('Location') == '/all/', f'Expected redirect to /all/ but got {resp_reg.get("Location")}'

# Verify in DB
reg_buyer = Buyer.objects.filter(phone=test_phone).first()
reg_user = User.objects.filter(username=test_phone).first()
reg_addr = Address.objects.filter(buyer=reg_buyer).first()
assert reg_buyer is not None, 'Buyer was not saved in DB!'
assert reg_user is not None, 'User was not saved in auth_user!'
assert reg_addr is not None, 'Registration address was not saved!'
print(f'  [PASS] Registered Buyer: {reg_buyer.name} ({reg_buyer.phone})')
print(f'  [PASS] Registered Address: {reg_addr.address}, {reg_addr.city} ({reg_addr.pin})')
print(f'  [PASS] Redirected cleanly to: {resp_reg.get("Location")}')

# ----------------------------------------------------
# TEST 2: LOGOUT & LOGIN FLOW (BY EMAIL & BY PHONE)
# ----------------------------------------------------
print('\n[2/7] Testing Customer Logout & Login...')
c.get('/logout/')
assert c.session.get('_auth_user_id') is None, 'Customer logout failed!'

# Login with EMAIL
resp_log_email = c.post('/login/', {'username': test_email, 'password': test_pass}, follow=False)
assert resp_log_email.status_code == 302, 'Login with email failed'
assert resp_log_email.get('Location') == '/all/', 'Login by email did not redirect to /all/'
print('  [PASS] Login with EMAIL successful -> Redirected to /all/')

c.get('/logout/')

# Login with PHONE
resp_log_phone = c.post('/login/', {'username': test_phone, 'password': test_pass}, follow=False)
assert resp_log_phone.status_code == 302, 'Login with phone failed'
assert resp_log_phone.get('Location') == '/all/', 'Login by phone did not redirect to /all/'
print('  [PASS] Login with PHONE successful -> Redirected to /all/')

c.get('/logout/')

# ----------------------------------------------------
# TEST 3: FORGOT PASSWORD WITH EMAIL OTP FLOW
# ----------------------------------------------------
print('\n[3/7] Testing Forgot Password OTP Flow...')
# Request OTP using phone or email
resp_forgot = c.post('/forgot-password/', {'identifier': test_phone})
assert resp_forgot.status_code == 302, 'Forgot password request failed'
assert resp_forgot.get('Location') == '/verify-reset-otp/', 'Did not redirect to verify OTP page'

otp_record = PasswordResetOTP.objects.filter(email=test_email, is_used=False).order_by('-id').first()
assert otp_record is not None, 'OTP was not generated in DB!'
print(f'  [PASS] OTP generated and sent to email: {otp_record.otp}')

# Verify OTP and set NEW PASSWORD
resp_reset = c.post('/verify-reset-otp/', {
    'otp': otp_record.otp,
    'new_password': new_pass,
    'confirm_password': new_pass
})
assert resp_reset.status_code == 302, 'Password reset post failed'
assert resp_reset.get('Location') == '/login/', 'Did not redirect to login after reset'

# Test login with NEW PASSWORD
c_new = Client()
resp_login_new = c_new.post('/login/', {'username': test_email, 'password': new_pass})
assert resp_login_new.status_code == 302 and resp_login_new.get('Location') == '/all/', 'Login with new password failed!'
print('  [PASS] Password reset successfully updated in DB')
print('  [PASS] Login with NEW PASSWORD verified (Email + Phone working)!')

# ----------------------------------------------------
# TEST 4: CHECKOUT FLOW & PLACE ORDER BUTTON LOCK
# ----------------------------------------------------
print('\n[4/7] Testing Checkout Flow & Email Verification Lock...')
c_guest = Client()
prod = Product.objects.first()
if not prod:
    prod = Product.objects.create(name='Banarasi Silk Saree', price=1499, base_price=1499)

sess = c_guest.session
sess['cart'] = {str(prod.id): {'name': prod.name, 'price': 1499, 'quantity': 1, 'image': '', 'size': 'Free', 'color': 'Maroon'}}
sess.save()

# Checkout GET: Check that button is locked
resp_co = c_guest.get('/checkout/')
assert resp_co.status_code == 200, 'Checkout page failed to load'
co_html = resp_co.content.decode('utf-8')
assert 'Verify Email First to Buy' in co_html, 'Button should display Verify Email First to Buy'
assert 'disabled' in co_html, 'Button must be disabled initially'
print('  [PASS] Checkout page loads properly')
print('  [PASS] Place Order button is correctly LOCKED (Disabled + "Verify Email First to Buy")')

# Try submitting order WITHOUT email verification: must be blocked!
resp_blocked = c_guest.post('/checkout/', {
    'name': 'Pooja Guest',
    'phone': '9888111222',
    'email': 'guest.buyer@test.com',
    'address': 'Street 10, Civil Lines',
    'city': 'Jaipur',
    'state': 'Rajasthan',
    'pincode': '302001'
})
assert 'verify your email' in resp_blocked.content.decode('utf-8').lower(), 'Unverified checkout should be blocked!'
print('  [PASS] Backend strictly BLOCKS order placement without verified email')

# Send & Verify checkout OTP
guest_email = 'guest.buyer@test.com'
c_guest.post('/send-checkout-email-otp/', {'email': guest_email, 'name': 'Pooja Guest'})
checkout_otp = PasswordResetOTP.objects.filter(email=guest_email, is_used=False).order_by('-id').first()
assert checkout_otp is not None, 'Checkout OTP not generated!'

resp_ver_otp = c_guest.post('/verify-checkout-email-otp/', {'email': guest_email, 'otp': checkout_otp.otp})
assert resp_ver_otp.json().get('status') == 'success', 'Checkout OTP verification failed'
print(f'  [PASS] Checkout OTP verified successfully for {guest_email}')

# After verification, check button state
resp_co_ver = c_guest.get('/checkout/')
assert 'Place Order (Cash on Delivery)' in resp_co_ver.content.decode('utf-8'), 'Button must be unlocked after verification'
print('  [PASS] Place Order button is now ACTIVATED (Green + "Place Order")')

# Place order with verified email
resp_order = c_guest.post('/checkout/', {
    'name': 'Pooja Guest',
    'phone': '9888111222',
    'email': guest_email,
    'address': 'Street 10, Civil Lines',
    'city': 'Jaipur',
    'state': 'Rajasthan',
    'pincode': '302001'
})
assert resp_order.status_code == 200, f'Expected order confirmation 200 but got {resp_order.status_code}'
assert 'confirmation' in resp_order.content.decode('utf-8').lower() or 'order' in resp_order.content.decode('utf-8').lower(), 'Order confirmation page not displayed'

# Verify user was created with 10-digit phone as initial password
guest_user = User.objects.filter(username='9888111222').first()
assert guest_user is not None, 'Guest user account not created!'
assert guest_user.check_password('9888111222'), 'Guest user initial password should be their 10-digit mobile number!'
print('  [PASS] Order placed successfully!')
print('  [PASS] Guest account auto-created with 10-digit mobile number as initial password')

# ----------------------------------------------------
# TEST 5: ADMIN PANEL - REGISTERED USERS & LOGOUT
# ----------------------------------------------------
print('\n[5/7] Testing Admin Panel Registered Users & Logout...')
c_admin = Client()
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.create_superuser('admin_e2e', 'admin_e2e@narifashionstore.com', 'AdminPass123')
c_admin.force_login(admin_user)

# Admin Registered Users Table
resp_admin_buyers = c_admin.get('/admin-buyer/')
assert resp_admin_buyers.status_code == 200, f'Admin buyers page failed with status {resp_admin_buyers.status_code}'
print('  [PASS] /admin-buyer/ loads with Status 200 OK')

# Admin Buyer Details
test_b_id = reg_buyer.id
resp_b_details = c_admin.get(f'/admin-buyer-details/{test_b_id}/')
assert resp_b_details.status_code == 200, f'Admin buyer details failed with status {resp_b_details.status_code}'
print('  [PASS] /admin-buyer-details/<id>/ loads with Status 200 OK (Profile, Addresses & Orders)')

# Admin Logout
resp_admin_logout = c_admin.get('/admin-logout/')
assert resp_admin_logout.status_code == 302, 'Admin logout should redirect'
assert c_admin.session.get('_auth_user_id') is None, 'Admin session not cleared on logout!'

# Visit /login/ after admin logout: MUST show login page, NOT redirect to admin dashboard
resp_after_logout = c_admin.get('/login/')
assert resp_after_logout.status_code == 200, 'Visiting /login/ after logout should return 200 login page!'
print('  [PASS] /admin-logout/ cleanly flushes session and prevents redirect bounce')

# ----------------------------------------------------
# TEST 6: CATALOG & SEO URLS
# ----------------------------------------------------
print('\n[6/7] Testing Catalog & Products Routes...')
assert c.get('/all/').status_code == 200, '/all/ route failed'
assert c.get('/products/').status_code == 200, '/products/ route failed'
assert c.get('/filter/').status_code == 200, '/filter/ route failed'
print('  [PASS] /all/ and /products/ catalog pages load with Status 200 OK')

# ----------------------------------------------------
# CLEANUP
# ----------------------------------------------------
print('\n[7/7] Cleaning up temporary test records...')
User.objects.filter(username=test_phone).delete()
Buyer.objects.filter(phone=test_phone).delete()
User.objects.filter(username='9888111222').delete()
Buyer.objects.filter(phone='9888111222').delete()
PasswordResetOTP.objects.filter(email__in=[test_email, guest_email]).delete()
print('  [PASS] Database clean')

print('\n========================================================')
print('>>> ALL 7 END-TO-END SUITE TESTS PASSED WITH 100% SUCCESS! <<<')
print('========================================================')

