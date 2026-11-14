// import { useEffect, useState } from "react";
// import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
// import { api, getToken, setToken } from "./api.js";
// import { Login, Register, Events, Gallery, Admin } from "./pages.jsx";

// export default function App() {
//   const [user, setUser] = useState(null);
//   const [ready, setReady] = useState(false);
//   const nav = useNavigate();

//   useEffect(() => {
//     if (!getToken()) return setReady(true);
//     api.me().then(setUser).catch(() => setToken(null)).finally(() => setReady(true));
//   }, []);

//   const onAuth = ({ token, user }) => {
//     setToken(token);
//     setUser(user);
//     nav("/");
//   };
//   const logout = () => {
//     setToken(null);
//     setUser(null);
//     nav("/login");
//   };

//   if (!ready) return null;

//   return (
//     <>
//       <header className="bar">
//         <Link to="/" className="brand">FaceFind</Link>
//         {user && (
//           <nav>
//             {user.is_admin && <Link to="/admin">Manage events</Link>}
//             <span className="who">{user.name}</span>
//             <button className="link" onClick={logout}>Log out</button>
//           </nav>
//         )}
//       </header>
//       <main>
//         <Routes>
//           <Route path="/login" element={<Login onAuth={onAuth} />} />
//           <Route path="/register" element={<Register onAuth={onAuth} />} />
//           <Route path="/" element={user ? <Events /> : <Navigate to="/login" />} />
//           <Route path="/events/:id" element={user ? <Gallery /> : <Navigate to="/login" />} />
//           <Route path="/admin" element={user?.is_admin ? <Admin /> : <Navigate to="/" />} />
//         </Routes>
//       </main>
//     </>
//   );
// }


import { useEffect, useState } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { api, getToken, setToken } from "./api.js";
import { Login, Register, Events, Gallery, Admin } from "./pages.jsx";
import { Brand } from "./scene.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const nav = useNavigate();
  const { pathname } = useLocation();
  const isAuth = pathname === "/login" || pathname === "/register";

  useEffect(() => {
    if (!getToken()) return setReady(true);
    api.me().then(setUser).catch(() => setToken(null)).finally(() => setReady(true));
  }, []);

  const onAuth = ({ token, user }) => {
    setToken(token);
    setUser(user);
    nav("/");
  };
  const logout = () => {
    setToken(null);
    setUser(null);
    nav("/login");
  };
  const deleteAccount = async () => {
    if (!window.confirm("Delete your account and face data? This can't be undone.")) return;
    await api.deleteMe();
    logout();
  };

  if (!ready) return null;

  const routes = (
    <Routes>
      <Route path="/login" element={<Login onAuth={onAuth} />} />
      <Route path="/register" element={<Register onAuth={onAuth} />} />
      <Route path="/" element={user ? <Events /> : <Navigate to="/login" />} />
      <Route path="/events/:id" element={user ? <Gallery /> : <Navigate to="/login" />} />
      <Route path="/admin" element={user?.is_admin ? <Admin /> : <Navigate to="/" />} />
    </Routes>
  );

  return (
    <>
      {!isAuth && (
        <header className="bar">
          <Brand />
          {user && (
            <nav>
              {user.is_admin && <a href="/admin" onClick={(e) => { e.preventDefault(); nav("/admin"); }}>Manage events</a>}
              <span className="who">{user.name}</span>
              <button className="link" onClick={deleteAccount}>Delete my data</button>
              <button className="link" onClick={logout}>Log out</button>
            </nav>
          )}
        </header>
      )}
      {isAuth ? routes : <main>{routes}</main>}
    </>
  );
}