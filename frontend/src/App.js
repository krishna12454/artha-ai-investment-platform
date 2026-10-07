import React, { useState } from "react";
import "@/App.css";
import { AnimatePresence, motion } from "framer-motion";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/context/ThemeContext";
import { Header } from "@/components/Header";
import PortfolioView from "@/views/PortfolioView";
import ValuationView from "@/views/ValuationView";
import InsightsView from "@/views/InsightsView";
import PipelinesView from "@/views/PipelinesView";
import MonitoringView from "@/views/MonitoringView";

const VIEWS = {
  "portfolio": PortfolioView,
  "ai-valuation": ValuationView,
  "market-insights": InsightsView,
  "data-pipelines": PipelinesView,
  "system-monitoring": MonitoringView,
};

function App() {
  const [active, setActive] = useState("portfolio");
  const View = VIEWS[active];

  return (
    <ThemeProvider>
      <div className="App min-h-screen grain">
        <Header active={active} onNavigate={setActive} />
        <main className="max-w-[1500px] mx-auto px-4 sm:px-6 py-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              <View />
            </motion.div>
          </AnimatePresence>
        </main>
        <footer className="max-w-[1500px] mx-auto px-6 py-8 border-t border-hair mt-8">
          <p className="text-xs text-muted-3">
            Artha AI — Investment Intelligence Platform · Live market data via Yahoo Finance (simulated fallback) ·
            AI engine: Anthropic Claude · Built for institutional research & portfolio workflows.
          </p>
        </footer>
        <Toaster theme="dark" position="bottom-right" richColors />
      </div>
    </ThemeProvider>
  );
}

export default App;
