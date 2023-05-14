(function () {
  "use strict";
  
  initalizeFirebase();
  document.getElementById("resend_verification_email").onclick = () => sendVerificationEmail(firebase.auth().currentUser);
})();

function initializeFirebase() {
  const firebaseConfig = {
    apiKey: "AIzaSyC1k5fAwQU_mHZ_kS9WMsgBd6Nl1i_8Vb0",
    authDomain: "n-glot.firebaseapp.com",
    projectId: "n-glot",
    storageBucket: "n-glot.appspot.com",
    messagingSenderId: "947090572647",
    appId: "1:947090572647:web:0838cd9ead0b2d9659dbc2",
    measurementId: "G-E4GRM7Q8XG"
  };
  const app = firebase.initializeApp(firebaseConfig);
}

function sendVerificationEmail(user) {
  user.sendEmailVerification().then(function () {
    console.log("Email Sent");
    // firebase.auth().onAuthStateChanged(function(user) {
    //   if (user) {
    //     if (user.emailVerified) {
    //       console.log("Email Verified");
    //     } else {
    //       console.log("Email Not Verified");
    //     }
    //   }
    // });
  });
}
