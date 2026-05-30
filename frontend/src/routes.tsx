import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { AsteroidProfilePage } from "@/pages/AsteroidProfilePage";
import { DomainExplorerPage } from "@/pages/DomainExplorerPage";
import { GNNResearchLabPage } from "@/pages/GNNResearchLabPage";
import { MethodologyPage } from "@/pages/MethodologyPage";
import { MissionControlPage } from "@/pages/MissionControlPage";
import { ModelAndLeakageLabPage } from "@/pages/ModelAndLeakageLabPage";
import { MonteCarloLabPage } from "@/pages/MonteCarloLabPage";
import { PipelineMonitorPage } from "@/pages/PipelineMonitorPage";
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
        { path: "ml-lab", element: <ModelAndLeakageLabPage /> },
        { path: "gnn", element: <GNNResearchLabPage /> },
        { path: "domain", element: <DomainExplorerPage /> },
        { path: "pipeline", element: <PipelineMonitorPage /> },
        { path: "methodology", element: <MethodologyPage /> }
      ]
    }
  ]);
