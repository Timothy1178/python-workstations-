const React = require("react"), ReactDOMServer = require("react-dom/server"), sharp = require("sharp"), fs = require("fs");
const fa = require("react-icons/fa");
const WANT = {
  whatsapp: "FaWhatsapp", qrcode: "FaQrcode", mobile: "FaMobileAlt", usercheck: "FaUserCheck", idcard: "FaIdCard",
  shield: "FaShieldAlt", language: "FaLanguage", headset: "FaHeadset", chart: "FaChartLine", clock: "FaClock",
  database: "FaDatabase", robot: "FaRobot", cloud: "FaCloud", sms: "FaSms", store: "FaStore", gift: "FaGift",
  lock: "FaLock", check: "FaCheckCircle", warning: "FaExclamationTriangle", users: "FaUsers", bolt: "FaBolt",
  smile: "FaSmile", clipboard: "FaClipboardList", filealt: "FaFileAlt", comments: "FaComments", cog: "FaCogs",
  arrow: "FaArrowRight", star: "FaStar", money: "FaDollarSign", handshake: "FaHandshake", flag: "FaFlagCheckered", search: "FaSearch", bullhorn: "FaBullhorn",
};
const COLORS = { red: "E31836", white: "FFFFFF", grey: "5F6062", green: "25D366", dark: "1F1F1F", gold: "C9A04B" };
(async () => {
  for (const [name, comp] of Object.entries(WANT)) {
    const Icon = fa[comp]; if (!Icon) { console.log("missing", comp); continue; }
    for (const [cn, hex] of Object.entries(COLORS)) {
      const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: 512 }));
      await sharp(Buffer.from(svg)).resize(512, 512, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toFile(`icons/${name}-${cn}.png`);
    }
  }
  console.log("icons:", fs.readdirSync("icons").length);
})();
