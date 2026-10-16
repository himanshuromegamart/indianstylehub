// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js');

firebase.initializeApp({
    apiKey: "AIzaSyC_xWf2ll2VGaRkFifvcgdKv_KJ7JB8bwI",
    authDomain: "alert-301c6.firebaseapp.com",
    projectId: "alert-301c6",
    storageBucket: "alert-301c6.appspot.com",
    messagingSenderId: "748950024046",
    appId: "1:748950024046:web:8b2bd867f2613774a9db7f",
    measurementId: "G-25Z0J5VN5H"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
    console.log('[firebase-messaging-sw.js] Received background message', payload);
    const notificationTitle = payload.notification?.title || 'Bharat Shop';
    const notificationOptions = {
        body: payload.notification?.body || '',
        icon: payload.notification?.icon || '/static/assets/img/logo.png',
        image: payload.notification?.image || '',
        data: {
            url: payload.data?.url || '/'
        }
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const targetUrl = event.notification.data?.url || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === targetUrl && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});

