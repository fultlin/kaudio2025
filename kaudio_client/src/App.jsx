import Layout from "./components/Layout/component";
import { RouterProvider } from "react-router-dom";
import router from "./routes/routes";
import "./App.module.scss";
import { observer } from "mobx-react-lite";
import authStore from "./stores/authStore";

function App() {
  return <RouterProvider router={router} />;
}

export default observer(App);
