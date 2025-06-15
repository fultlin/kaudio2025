import { createBrowserRouter } from "react-router-dom";
import ErrorPage from "../components/ErrorPage/component";
import Layout from "../components/Layout/component";
import Music from "../components/Music/component";
import Register from "../components/Register/component";
import LoginForm from "../components/Login/component";
import Home from "../components/Home/component";
import UploadForm from "../components/UploadForm/component";
import Settings from "../components/Settings/component";
import UploadTrack from "../components/UploadTrack/component";
import UploadAlbum from "../components/UploadAlbum/component";
import AlbumWithPlayer from "../components/Album";
import Playlists from "../components/Playlists/component";
import CreatePlaylist from "../components/Playlists/CreatePlaylist";
import EditPlaylist from "../components/Playlists/EditPlaylist";
import PlaylistView from "../components/Playlists/PlaylistView";
import Artist from "../components/Artist/component";
import StatisticsPage from "../components/Statistics";
import SearchPage from "../components/SearchPage/component";
import TrackPage from "../pages/TrackPage/component";
import AlbumPage from "../pages/AlbumPage/component";
import EditTrackPage from "../pages/EditTrackPage/component";
import EditAlbumPage from "../pages/EditAlbumPage/component";
import UserManagement from "../components/UserManagement/component";
import AnalyticsPage from "../pages/AnalyticsPage/component";

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
        element: <Music />,
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
      {
        path: "album/:id",
        element: <AlbumWithPlayer />,
      },
      {
        path: "playlists",
        element: <Playlists />,
      },
      {
        path: "playlists/create",
        element: <CreatePlaylist />,
      },
      {
        path: "playlists/:id",
        element: <PlaylistView />,
      },
      {
        path: "playlists/:id/edit",
        element: <EditPlaylist />,
      },
      {
        path: "artist/:id",
        element: <Artist />,
      },
      {
        path: "statistics",
        element: <StatisticsPage />,
      },
      {
        path: "search",
        element: <SearchPage />,
      },
      {
        path: "tracks/:id",
        element: <TrackPage />,
      },
      {
        path: "tracks/:id/edit",
        element: <EditTrackPage />,
      },
      {
        path: "albums/:id",
        element: <AlbumPage />,
      },
      {
        path: "albums/:id/edit",
        element: <EditAlbumPage />,
      },
      {
        path: "profile",
        element: <Settings />,
      },
      {
        path: "admin/users",
        element: <UserManagement />,
      },
      {
        path: "analytics",
        element: <AnalyticsPage />,
      },
    ],
  },
]);

export default router;
