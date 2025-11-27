import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import SignupPage from "./components/SignupPage";
import AiStudioPage from "./components/AiStudioPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SignupPage />} />
        <Route path="/ai-studio" element={<AiStudioPage />} />
      </Routes>
    </BrowserRouter>
  );
}
