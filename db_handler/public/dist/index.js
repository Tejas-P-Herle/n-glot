import{initializeApp as e}from"https://www.gstatic.com/firebasejs/9.0.2/firebase-app.js";import{getAuth as o,signOut as s}from"https://www.gstatic.com/firebasejs/9.0.2/firebase-auth.js";!function(){"use strict";e({apiKey:"AIzaSyC1k5fAwQU_mHZ_kS9WMsgBd6Nl1i_8Vb0",authDomain:"n-glot.firebaseapp.com",projectId:"n-glot",storageBucket:"n-glot.appspot.com",messagingSenderId:"947090572647",appId:"1:947090572647:web:0838cd9ead0b2d9659dbc2",measurementId:"G-E4GRM7Q8XG"});const t=o();document.getElementById("signout").onclick=()=>{console.log("Signing Out"),s(t).then(()=>console.log("Signed Out"),()=>console.error("Error Signing Out"))}}();