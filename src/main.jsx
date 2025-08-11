import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom"; // Sadece BrowserRouter'ı import ediyoruz
import App from "./app.jsx"; // App bileşeni tüm rotaları içerecek
import "./index.css"; // Tailwind burada bağlanıyor

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <BrowserRouter> {/* Uygulamanın tamamını tek bir BrowserRouter ile sarıyoruz */}
      <App /> {/* App bileşeni kendi içinde Routes ve Route'ları yönetecek */}
    </BrowserRouter>
  </React.StrictMode>
);
