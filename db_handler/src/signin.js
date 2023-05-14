
(function() {
  "use strict";

  // Authentication code taken from -> https://firebase.google.com/docs/auth/web/firebaseui
  const app = initializeFirebase();
  checkSignedIn();

  var ui = new firebaseui.auth.AuthUI(firebase.auth());
  var uiConfig = {
    callbacks: {
      signInSuccessWithAuthResult: function(authResult, redirectUrl) {
        // User successfully signed in.
        // Return type determines whether we continue the redirect automatically
        // or whether we leave that to developer to handle.
        var user = authResult.user;
        if (authResult.additionalUserInfo.isNewUser) {
          console.log("new signin");
          if (!user.emailVerified) {
            sendVerificationEmail(user);
            console.log("Email Not Verified");
            window.location.replace("/verify-email.html");
          }
        } else if (user.emailVerified) {
          console.log("Email Verified");
          window.location.replace("/");
        } else {
          console.log("Email Not Verified");
          window.location.replace("/verify-email.html");
        }
        // return true;
      },
      uiShown: function() {
        // The widget is rendered.
        // Hide the loader.
        document.getElementById('loader').style.display = 'none';
      }
    },
    // Will use popup for IDP Providers sign-in flow instead of the default, redirect.
    // signInFlow: 'popup',
    signInSuccessUrl: '/',
    signInOptions: [
      // Leave the lines as is for the providers you want to offer your users.
      firebase.auth.EmailAuthProvider.PROVIDER_ID,
      firebase.auth.GoogleAuthProvider.PROVIDER_ID,
      // firebase.auth.FacebookAuthProvider.PROVIDER_ID,
      // firebase.auth.TwitterAuthProvider.PROVIDER_ID,
      // firebase.auth.GithubAuthProvider.PROVIDER_ID,
      // firebase.auth.EmailAuthProvider.PROVIDER_ID,
      // firebase.auth.PhoneAuthProvider.PROVIDER_ID
    ],
    tosUrl: '/terms-of-service',
    privacyPolicyUrl: '/privacy-policy'
  };

  // The start method will wait until the DOM is loaded.
  ui.start('#firebaseui-auth-container', uiConfig);

})();

function initializeFirebase() {
  return firebase.initializeApp({
    apiKey: "AIzaSyC1k5fAwQU_mHZ_kS9WMsgBd6Nl1i_8Vb0",
    authDomain: "n-glot.firebaseapp.com",
    projectId: "n-glot",
    storageBucket: "n-glot.appspot.com",
    messagingSenderId: "947090572647",
    appId: "1:947090572647:web:0838cd9ead0b2d9659dbc2",
    measurementId: "G-E4GRM7Q8XG"
  });
}

function sendVerificationEmail(user) {
  user.sendEmailVerification().then(() => { console.log("Email Sent"); });
}

function checkSignedIn() {
  firebase.auth().onAuthStateChanged((user) => {
    if (user && user.emailVerified) document.location.replace("/");
  });
}
