const React = require("react"), ReactDOMServer = require("react-dom/server"), sharp = require("sharp"), fs = require("fs");
const fa = require("react-icons/fa");
const WANT = {
  whatsapp: "FaWhatsapp", qrcode: "FaQrcode", mobile: "FaMobileAlt", usercheck: "FaUserCheck", idcard: "FaIdCard",
  shield: "FaShieldAlt", language: "FaLanguage", headset: "FaHeadset", chart: "FaChartLine", clock: "FaClock",
  database: "FaDatabase", robot: "FaRobot", cloud: "FaCloud", sms: "FaSms", store: "FaStore", gift: "FaGift",
  lock: "FaLock", check: "FaCheckCircle", warning: "FaExclamationTriangle", users: "FaUsers", bolt: "FaBolt",
  smile: "FaSmile", clipboard: "FaClipboardList", filealt: "FaFileAlt", comments: "FaComments", cog: "FaCogs",
  arrow: "FaArrowRight", star: "FaStar", money: "FaDollarSign", handshake: "FaHandshake", flag: "FaFlagCheckered", search: "FaSearch", bullhorn: "FaBullhorn",
  paperplane: "FaPaperPlane", cog1: "FaCog", image: "FaImage", quote: "FaQuoteLeft", user: "FaUser", check2: "FaCheck", times: "FaTimes",
  laptop: "FaLaptop", play: "FaPlay", lightbulb: "FaLightbulb", rocket: "FaRocket", heart: "FaHeart", trophy: "FaTrophy", globe: "FaGlobe",
  sync: "FaSyncAlt", layer: "FaLayerGroup", palette: "FaPalette", magic: "FaMagic", link: "FaLink", table: "FaTable", chartpie: "FaChartPie",
  sitemap: "FaSitemap", th: "FaTh", camera: "FaCamera", mousepointer: "FaMousePointer", font: "FaFont", film: "FaFilm", leaf: "FaLeaf", map: "FaMapMarkerAlt",
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
  // grey image placeholders (real pictures, so "Change Picture" works in PowerPoint)
  for (const [name, w, h] of [["ph-wide", 1600, 1000], ["ph-square", 1000, 1000], ["ph-tall", 1000, 1400]]) {
    const ic = ReactDOMServer.renderToStaticMarkup(React.createElement(fa.FaImage, { color: "#B9BDC4", size: Math.round(Math.min(w, h) * 0.28) }));
    const icon = await sharp(Buffer.from(ic)).png().toBuffer();
    const meta = await sharp(icon).metadata();
    await sharp({ create: { width: w, height: h, channels: 4, background: "#E9EBEE" } })
      .composite([{ input: icon, left: Math.round((w - meta.width) / 2), top: Math.round((h - meta.height) / 2) }]).png().toFile(`icons/${name}.png`);
  }
  console.log("icons:", fs.readdirSync("icons").length);
})();
