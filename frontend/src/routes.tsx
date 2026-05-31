import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { AsteroidProfilePage } from "@/pages/AsteroidProfilePage";
import { FindingsPage } from "@/pages/FindingsPage";
import { GNNResearchLabPage } from "@/pages/GNNResearchLabPage";
import { MethodologyPage } from "@/pages/MethodologyPage";
import { MissionControlPage } from "@/pages/MissionControlPage";
import { MonteCarloLabPage } from "@/pages/MonteCarloLabPage";
import { OrbitalSimulationPage } from "@/pages/OrbitalSimulationPage";
import { RiskRankingPage } from "@/pages/RiskRankingPage";

export const createAppRouter = () =>
  createBrowserRouter([
    {
      path: "/",
      element: <AppShell />,
      children: [
        { index: true, element: <MissionControlPage /> },
        { path: "ranking", element: <RiskRankingPage /> },
        { path: "objects", element: <AsteroidProfilePage /> },
        { path: "objects/:objectKey", element: <AsteroidProfilePage /> },
        { path: "monte-carlo", element: <MonteCarloLabPage /> },
        { path: "orbital-simulation", element: <OrbitalSimulationPage /> },
        { path: "gnn", element: <GNNResearchLabPage /> },
        { path: "findings", element: <FindingsPage /> },
        { path: "methodology", element: <MethodologyPage /> }
      ]
    }
  ]);
