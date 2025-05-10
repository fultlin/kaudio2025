import { createBrowserRouter } from "react-router-dom";
import ErrorPage from "../components/ErrorPage/component";
import Layout from "../components/Layout/component";
import Music from "../components/Favourite/component";
import Register from "../components/Register/component";
import LoginForm from "../components/Login/component";
import Home from "../components/Home/component";
import UploadForm from "../components/UploadForm/component";
import Settings from "../components/Settings/component";
import UploadTrack from "../components/UploadTrack/component";
import UploadAlbum from "../components/UploadAlbum/component";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    errorElement: <ErrorPage />,
    children: [
      {
        path: "/",
        element: <Home />,
      },
      {
        path: "music",
        element: <div>music</div>,
      },
      {
        path: "register",
        element: <Register />,
      },
      {
        path: "auth",
        element: <LoginForm />,
      },
      {
        path: "upload",
        element: <UploadForm />,
      },
      {
        path: "upload/track",
        element: <UploadTrack />,
      },
      {
        path: "upload/album",
        element: <UploadAlbum />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
    ],
  },
]);

export default router;
