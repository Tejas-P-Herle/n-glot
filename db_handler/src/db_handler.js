// Import the functions you need from the SDKs you need
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.0.2/firebase-app.js';
import { getAuth, signInWithEmailAndPassword } from 'https://www.gstatic.com/firebasejs/9.0.2/firebase-auth.js';

// firestore-lite is Restrictive, but faster and smaller. For More Info,
// Read: https://firebase.google.com/docs/firestore/solutions/firestore-lite
import { getFirestore, collection, doc, getDoc, getDocs, updateDoc, setDoc, deleteDoc, query, where } from 'https://www.gstatic.com/firebasejs/9.0.2/firebase-firestore.js';


export class DBHandler {
  constructor() {
    // Follow this pattern to import other Firebase services
    // import { } from 'firebase/<service>';

    const firebaseConfig = {
      apiKey: "AIzaSyC1k5fAwQU_mHZ_kS9WMsgBd6Nl1i_8Vb0",
      authDomain: "n-glot.firebaseapp.com",
      projectId: "n-glot",
      storageBucket: "n-glot.appspot.com",
      messagingSenderId: "947090572647",
      appId: "1:947090572647:web:0838cd9ead0b2d9659dbc2",
      measurementId: "G-E4GRM7Q8XG"
    };
    const app = initializeApp(firebaseConfig);
    const auth = getAuth();
    this.db = getFirestore();
    this.auth = auth;
  }

  async signIn(username, password) {
    if (username && password) {
      await signInWithEmailAndPassword(this.auth, username, password);
    }
  }

  async get_package(language, package_name="basic") {
    var doc_ref = doc(this.db, "languages", language, "packages", package_name);
    return (await getDoc(doc_ref)).data();
  }

  async get_langs_meta() {
    var docs_ref = getDocs(collection(this.db, "languages"));
    var docs_data = {};
    for (const doc_ref of (await docs_ref).docs) 
      docs_data[doc_ref.id] = doc_ref.data();
    return docs_data;
  }

  async get_basic_funcs(language_from, language_to) {

    var basic_funcs = {"from": {}, "to": {"convs": {}, "obj_mod_convs": {}, "func_call_convs": {}, "lib_convs": {}}};
    var from_docs_ref = getDocs(collection(
      this.db, "languages", language_from, "from"));
    for (const func_ref of (await from_docs_ref).docs) {
      if (func_ref.id != "Coll-Bridge") basic_funcs["from"][func_ref.id] = func_ref.data();
    }

    var to_docs_ref = getDocs(collection(
      this.db, "languages", language_to, "to", "Coll-Bridge", language_from,
      "Coll-Bridge", "reserved"));
    for (const func_ref of (await to_docs_ref).docs) {
      if (func_ref.id != "Coll-Bridge") basic_funcs["to"][func_ref.id] = func_ref.data();
    }

    var to_docs_ref = getDocs(collection(
      this.db, "languages", language_to, "to", "Coll-Bridge", language_from,
      "Coll-Bridge", "misc"));
    for (const func_ref of (await to_docs_ref).docs) {
      if (func_ref.id != "Coll-Bridge") basic_funcs["to"]["convs"][func_ref.id] = func_ref.data();
    }
    var to_docs_ref = getDocs(collection(
      this.db, "languages", language_to, "to", "Coll-Bridge", language_from,
      "Coll-Bridge", "obj_mod"));
    for (const func_ref of (await to_docs_ref).docs) {
      if (func_ref.id != "Coll-Bridge") basic_funcs["to"]["obj_mod_convs"][func_ref.id] = func_ref.data();
    }
    var to_docs_ref = getDocs(collection(
      this.db, "languages", language_to, "to", "Coll-Bridge", language_from,
      "Coll-Bridge", "func_call"));
    for (const func_ref of (await to_docs_ref).docs) {
      if (func_ref.id != "Coll-Bridge") basic_funcs["to"]["func_call_convs"][func_ref.id] = func_ref.data();
    }
    var to_docs_ref = getDocs(collection(
      this.db, "languages", language_to, "to", "Coll-Bridge", language_from,
      "Coll-Bridge", "lib_convs"));
    for (const func_ref of (await to_docs_ref).docs) {
      if (func_ref.id != "Coll-Bridge") basic_funcs["to"]["lib_convs"][func_ref.id] = func_ref.data();
    }
    return basic_funcs;
  }

  async get_docs_json(...reference) {
    var docs_json = {};
    var docs_ref = await getDocs(collection(this.db, ...reference));
    for (var doc_ref of docs_ref.docs) docs_json[doc_ref.id] = doc_ref.data();
    return docs_json;
  }

  async get_doc_data(...reference) {
    return (await getDoc(doc(this.db, ...reference))).data();
  }

  get_collection(...collection_path) {
    return collection(this.db, ...collection_path);
  }

  async list_docs(collection_ref) {
    var collection_docs = await getDocs(collection_ref);
    console.log(collection_docs.docs.map(doc => doc.data()));
  }

  async get_doc(...doc_path) {
    var docPromise = getDoc(doc(this.db, ...doc_path));
    docPromise.catch(function (error) { console.error(error); });
    return docPromise;
  }

  async get_docs(...reference) {
    return getDocs(...reference);
  }

  async update_doc(data, ...doc_path) {
    return updateDoc(doc(this.db, ...doc_path), data);
  }

  async set_doc(data, ...doc_path) {
    return setDoc(doc(this.db, ...doc_path), data);
  }

  async delete_doc(...doc_path) {
    return deleteDoc(this.get_doc(...doc_path));
  }

  get_query(coll, query_obj) {
    return query(coll, query_obj);
  }

  where_constraint(field_id, operator, field_value) {
    return where(field_id, operator, field_value);
  }
}


(function() {
  window.DBHandler = DBHandler;
})();
