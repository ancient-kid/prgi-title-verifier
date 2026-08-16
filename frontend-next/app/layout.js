import { Outfit, Plus_Jakarta_Sans, JetBrains_Mono, Playfair_Display } from "next/font/google";
import "./globals.css";
import { TabProvider } from "@/context/TabContext";
import AmbientGlow from "@/components/AmbientGlow";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import TabContent from "@/components/TabContent";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-outfit",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["700", "800"],
  variable: "--font-playfair",
  display: "swap",
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plus-jakarta",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata = {
  title: "PRGI Title Verification System | Press Registrar General of India",
  description:
    "Automated AI and Rule-Based Title Verification Engine for the Press Registrar General of India (PRGI) under PRP Act 2023.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${playfair.variable} ${plusJakartaSans.variable} ${jetbrainsMono.variable}`}
    >
      <body>
        <TabProvider>
          <AmbientGlow />
          <div className="app-layout">
            <Navbar statusLabel="160k+ Titles Indexed" />
            <TabContent />
            <Footer />
          </div>
        </TabProvider>
      </body>
    </html>
  );
}
