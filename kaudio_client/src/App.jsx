import { RouterProvider } from "react-router-dom";
import { observer } from "mobx-react-lite";
import router from "./routes/routes";
import "./App.module.scss";

const App = observer(() => {
  return <RouterProvider router={router} />;
});

export default App;
