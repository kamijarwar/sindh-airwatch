import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const QUICK_CITIES = [
  { key: "Karachi", ur: "کراچی", sd: "ڪراچي", ru: "Karachi", en: "Karachi" },
  { key: "Hyderabad", ur: "حیدرآباد", sd: "حيدرآباد", ru: "Hyderabad", en: "Hyderabad" },
  { key: "Sukkur", ur: "سکھر", sd: "سکر", ru: "Sukkur", en: "Sukkur" },
  { key: "Larkana", ur: "لاڑکانہ", sd: "لاڙڪاڻو", ru: "Larkana", en: "Larkana" },
  { key: "Mirpur Khas", ur: "میرپور خاص", sd: "ميرپورخاص", ru: "Mirpur Khas", en: "Mirpur Khas" },
  { key: "Nawabshah", ur: "نوابشاہ", sd: "نوابشاهه", ru: "Nawabshah", en: "Nawabshah" },
  { key: "Jacobabad", ur: "جیکب آباد", sd: "جيڪب آباد", ru: "Jacobabad", en: "Jacobabad" },
  { key: "Khairpur", ur: "خیرپور", sd: "خيرپور", ru: "Khairpur", en: "Khairpur" },
  { key: "Dadu", ur: "دادو", sd: "دادو", ru: "Dadu", en: "Dadu" },
  { key: "Thatta", ur: "ٹھٹھہ", sd: "ٺٽو", ru: "Thatta", en: "Thatta" },
  { key: "Badin", ur: "بدین", sd: "بدين", ru: "Badin", en: "Badin" },
  { key: "Sanghar", ur: "سانگھڑ", sd: "سانگهڙ", ru: "Sanghar", en: "Sanghar" },
  { key: "Shikarpur", ur: "شکارپور", sd: "شڪارپور", ru: "Shikarpur", en: "Shikarpur" },
  { key: "Ghotki", ur: "گھوٹکی", sd: "گهوٽڪي", ru: "Ghotki", en: "Ghotki" },
  { key: "Jamshoro", ur: "جامشورو", sd: "ڄامشورو", ru: "Jamshoro", en: "Jamshoro" },
  { key: "Umerkot", ur: "عمرکوٹ", sd: "عمرڪوٽ", ru: "Umerkot", en: "Umerkot" },
  { key: "Mithi", ur: "مٹھی", sd: "مٺي", ru: "Mithi", en: "Mithi" },
  { key: "Tando Allahyar", ur: "ٹنڈو اللہ یار", sd: "ٽنڊو الهيار", ru: "Tando Allahyar", en: "Tando Allahyar" },
];

const AQI_SCALE = [
  { key: "good", range: "0 – 50", color: "#16a34a" },
  { key: "mod", range: "51 – 100", color: "#ca8a04" },
  { key: "usg", range: "101 – 150", color: "#ea580c" },
  { key: "unh", range: "151 – 200", color: "#dc2626" },
  { key: "vunh", range: "201 – 300", color: "#9333ea" },
  { key: "haz", range: "301+", color: "#881337" },
];

const STARS = [
  { top: "14%", left: "12%", delay: "0s" },
  { top: "24%", left: "26%", delay: "0.9s" },
  { top: "10%", left: "44%", delay: "1.6s" },
  { top: "28%", left: "58%", delay: "0.4s" },
  { top: "16%", left: "72%", delay: "2.1s" },
  { top: "36%", left: "84%", delay: "1.2s" },
  { top: "40%", left: "18%", delay: "2.4s" },
  { top: "18%", left: "90%", delay: "0.7s" },
];

const GLOBAL_STARS = [
  { top: "6%", left: "8%", delay: "0.2s" },
  { top: "12%", left: "92%", delay: "1.1s" },
  { top: "22%", left: "4%", delay: "1.8s" },
  { top: "30%", left: "95%", delay: "0.5s" },
  { top: "48%", left: "6%", delay: "2.2s" },
  { top: "55%", left: "93%", delay: "1.4s" },
  { top: "72%", left: "9%", delay: "0.8s" },
  { top: "80%", left: "91%", delay: "2.6s" },
];

const RAIN_DROPS = [
  { left: "10%", delay: "0s" },
  { left: "20%", delay: "0.35s" },
  { left: "32%", delay: "0.7s" },
  { left: "45%", delay: "0.15s" },
  { left: "57%", delay: "0.55s" },
  { left: "68%", delay: "0.85s" },
  { left: "79%", delay: "0.25s" },
  { left: "90%", delay: "0.6s" },
];

const TEXT = {
  ur: {
    rtl: true,
    brand: "سندھ ایئر واچ",
    sub: "سندھ بھر کی لائیو ہوا اور AI پیشن گوئی",
    placeholder: "سندھ کا کوئی شہر یا علاقہ لکھیں (مثلاً کراچی، کلفٹن، نوابشاہ)...",
    search: "تلاش کریں",
    gps: "📍 میری لوکیشن",
    quickLabel: "ایک کلک میں اپنا شہر منتخب کریں:",
    tabLive: "لائیو اور پیشن گوئی",
    tabRank: "سندھ رینکنگ (20 شہر)",
    tabTrends: "تاریخی رجحان",
    tabAbout: "ہمارے بارے میں",
    updated: "تازہ ترین",
    groundSrc: (n) => `لائیو گراؤنڈ سینسرز (${n})`,
    modelSrc: "سیٹلائٹ + AI ماڈل",
    sky: {
      clearDay: "صاف دھوپ",
      clearNight: "صاف رات",
      partly: "جزوی بادل",
      cloudy: "بادل چھائے ہوئے",
      fog: "دھند / اسموگ",
      rain: "بارش",
      storm: "آندھی اور گرج چمک",
    },
    temp: "درجہ حرارت",
    feels: "محسوس گرمی",
    hum: "نمی",
    wind: "ہوا کی رفتار",
    rain: "بارش کا امکان",
    adviceTitle: "صحت کے لیے الگ الگ ہدایات",
    adviceSub: "موجودہ ہوا کے معیار کے مطابق احتیاطی تدابیر",
    adviceLabels: {
      mask: "ماسک",
      outdoor: "باہر جانا / ورزش",
      sensitive: "بچے، بزرگ اور دمہ",
      windows: "گھر کی کھڑکیاں",
    },
    tomTitle: "کل کی AI پیشن گوئی",
    tomTag: "Random Forest ML",
    todayAqi: "آج کا تخمینہ",
    tomAqi: "کل کا متوقع AQI",
    tomTemp: "کل کا درجہ حرارت",
    tomRain: "کل بارش",
    tomGain: (g) => `ماڈل بہتری: +${g}%`,
    noTom: "اس علاقے کے لیے کل کی AI پیشن گوئی ابھی دستیاب نہیں — اوپر 24 گھنٹے کی پٹی دیکھیں۔",
    stripTitle: "اگلے 24 گھنٹوں کی ہوا اور موسم",
    now: "ابھی",
    sensorsTitle: "قریبی لائیو سینسرز (OpenAQ)",
    noSensors: "اس علاقے کے قریب کوئی فعال گراؤنڈ سینسر نہیں ملا، اس لیے AI/سیٹلائٹ ڈیٹا دکھایا جا رہا ہے۔",
    kmAway: "کلومیٹر دور",
    hrsAgo: "گھنٹے پہلے",
    rankTitle: "سندھ کے 20 شہروں کی تازہ رینکنگ",
    rankSub: "سب سے صاف ہوا اوپر ہے — تفصیل دیکھنے کے لیے کسی بھی شہر پر کلک کریں",
    trendsTitle: "ہوا کے معیار کا رجحان",
    selectCity: "شہر منتخب کریں:",
    cleanest24: "گزشتہ 24 گھنٹے میں سب سے صاف وقت",
    peak24: "گزشتہ 24 گھنٹے میں سب سے زیادہ آلودگی",
    chart72: "گزشتہ 72 گھنٹوں کا AQI گراف",
    chart30: "گزشتہ 30 دنوں کا روزانہ اوسط AQI",
    aboutTitle: "سندھ ایئر واچ کے بارے میں",
    aboutSub: "سندھ کے شہریوں کے لیے تیز، سادہ اور قابلِ اعتماد فضائی آلودگی مانیٹرنگ",
    aboutMissionTitle: "یہ ایپ کیوں بنائی گئی؟",
    aboutMissionText:
      "سندھ ایئر واچ کا مقصد سندھ کے ہر شہر اور علاقے کے لوگوں کو اردو، سندھی، رومن اردو اور انگلش میں ہوا کے معیار اور اگلے دن کی AI پیشن گوئی آسانی سے فراہم کرنا ہے تاکہ ہر کوئی بروقت اپنی صحت کی حفاظت کر سکے۔",
    aboutDataTitle: "ڈیٹا اور AI ماڈلز",
    aboutDataPoints: [
      "OpenAQ لائیو گراؤنڈ سینسرز (جہاں دستیاب ہوں)",
      "Open-Meteo سیٹلائٹ اور موسم کا لائیو ڈیٹا",
      "سندھ کے 20 شہروں کے لیے مقامی Random Forest ML ماڈلز",
      "US EPA معیار کے مطابق PM2.5 سے AQI حساب",
    ],
    aboutAccessTitle: "سب کے لیے آسان استعمال",
    aboutAccessPoints: [
      "ایک کلک میں سندھ کے بڑے شہروں کا انتخاب",
      "GPS کے ذریعے قریبی شہر کی خودکار شناخت",
      "چار زبانوں (اردو، سندھی، رومن اردو، انگلش) میں مکمل سہولت",
    ],
    scaleTitle: "US AQI کے رنگوں کا چارٹ",
    loading: "ڈیٹا لوڈ ہو رہا ہے...",
    notFound: "یہ جگہ سندھ میں نہیں ملی۔ نیچے دیے گئے مشورے آزمائیں:",
    apiErr: "بیک اینڈ سرور سے رابطہ نہیں ہو سکا۔ چیک کریں کہ Python والا CMD کھلا ہوا ہے۔",
    gpsErr: "لوکیشن حاصل نہیں ہو سکی، براہِ کرم اپنا شہر خود منتخب کریں۔",
    footer: "Sindh AirWatch • Open-Meteo + OpenAQ + مقامی Random Forest ML ماڈلز",
    cats: {
      good: {
        label: "بہترین (صاف ہوا)",
        summary: "ہوا بالکل صاف ہے — باہر کی تمام سرگرمیاں محفوظ ہیں۔",
        cards: {
          mask: "ماسک پہننے کی ضرورت نہیں۔",
          outdoor: "واک، دوڑ اور کھیل کود کے لیے بہترین وقت ہے۔",
          sensitive: "بچوں، بزرگوں اور سانس کے مریضوں کے لیے مکمل محفوظ۔",
          windows: "تازہ ہوا کے لیے گھر کی کھڑکیاں کھلی رکھیں۔",
        },
      },
      mod: {
        label: "مناسب",
        summary: "عام لوگوں کے لیے ہوا ٹھیک ہے، حساس افراد ہلکی احتیاط کریں۔",
        cards: {
          mask: "عام افراد کو ضرورت نہیں؛ دھول والی سڑک پر ہلکا ماسک مفید ہے۔",
          outdoor: "باہر جا سکتے ہیں، لیکن زیادہ لمبی سخت ورزش سے گریز کریں۔",
          sensitive: "دمے یا الرجی کے مریض باہر زیادہ دیر رہنے میں احتیاط کریں۔",
          windows: "صبح اور شام کے وقت کھڑکیاں کھولی جا سکتی ہیں۔",
        },
      },
      usg: {
        label: "حساس افراد کے لیے نقصان دہ",
        summary: "بچوں، بزرگوں اور سانس کے مریضوں کو احتیاط کی ضرورت ہے۔",
        cards: {
          mask: "حساس افراد اور موٹر سائیکل سوار باہر ماسک ضرور پہنیں۔",
          outdoor: "باہر زیادہ محنت والی ورزش اور کھیل کم کریں۔",
          sensitive: "بچے، بزرگ اور دمے کے مریض انہیلر ساتھ رکھیں اور اندر رہیں۔",
          windows: "گرد اور دھویں سے بچنے کے لیے کھڑکیاں زیادہ تر بند رکھیں۔",
        },
      },
      unh: {
        label: "غیر صحت بخش",
        summary: "ہوا آلودہ ہے — ہر شخص کو باہر نکلتے وقت احتیاط کرنی چاہیے۔",
        cards: {
          mask: "باہر نکلتے وقت N95 یا KN95 ماسک لازمی پہنیں۔",
          outdoor: "باہر کی ورزش اور غیر ضروری چہل قدمی ملتوی کر دیں۔",
          sensitive: "بچوں، بزرگوں اور دل/پھیپھڑوں کے مریضوں کو گھر کے اندر رکھیں۔",
          windows: "کھڑکیاں اور دروازے اچھی طرح بند رکھیں۔",
        },
      },
      vunh: {
        label: "انتہائی غیر صحت بخش",
        summary: "ہوا شدید آلودہ ہے — غیر ضروری گھر سے باہر نہ نکلیں۔",
        cards: {
          mask: "انتہائی مجبوری میں باہر نکلیں تو فٹ N95 ماسک پہنیں۔",
          outdoor: "ہر قسم کی بیرونی سرگرمی اور کھیل کود مکمل بند رکھیں۔",
          sensitive: "بچوں، بزرگوں اور مریضوں پر خاص نظر رکھیں اور باہر نہ جانے دیں۔",
          windows: "کھڑکیاں مکمل بند رکھیں اور ممکن ہو تو ایئر پیوریفائر چلائیں۔",
        },
      },
      haz: {
        label: "خطرناک",
        summary: "ہنگامی حالت: فضا خطرناک حد تک آلودہ ہے۔",
        cards: {
          mask: "کسی بھی صورت میں باہر جانا پڑے تو صرف N95/P100 ماسک پہنیں۔",
          outdoor: "باہر نکلنا مکمل طور پر ترک کر دیں۔",
          sensitive: "سانس میں تکلیف ہو تو فوری ڈاکٹر سے رجوع کریں۔",
          windows: "تمام کھڑکیاں اور دروازے سیل بند رکھیں۔",
        },
      },
    },
  },
  sd: {
    rtl: true,
    brand: "سنڌ ايئر واچ",
    sub: "سنڌ جي لائيو هوا ۽ AI اڳڪٿي",
    placeholder: "سنڌ جو ڪو شهر يا علائقو لکو (مثال: ڪراچي، حيدرآباد، نوابشاهه)...",
    search: "ڳوليو",
    gps: "📍 منهنجي لوڪيشن",
    quickLabel: "هڪ ڪلڪ ۾ پنهنجو شهر چونڊيو:",
    tabLive: "لائيو ۽ اڳڪٿي",
    tabRank: "سنڌ رينڪنگ (20 شهر)",
    tabTrends: "تاريخي لاڙو",
    tabAbout: "اسان بابت",
    updated: "تازو اپڊيٽ",
    groundSrc: (n) => `لائيو گرائونڊ سينسرز (${n})`,
    modelSrc: "سيٽلائيٽ + AI ماڊل",
    sky: {
      clearDay: "صاف اس",
      clearNight: "صاف رات",
      partly: "ٿورا ڪڪر",
      cloudy: "ڪڪر ڇانيل",
      fog: "ڌنڌ / اسموگ",
      rain: "برسات",
      storm: "طوفان ۽ گجگوڙ",
    },
    temp: "گرمي پد",
    feels: "محسوس گرمي",
    hum: "گھم (نمی)",
    wind: "هوا جي رفتار",
    rain: "برسات جو امڪان",
    adviceTitle: "صحت لاءِ الڳ الڳ هدايتون",
    adviceSub: "موجوده هوا جي معيار موجب احتياطي تدبيرون",
    adviceLabels: {
      mask: "ماسڪ",
      outdoor: "ٻاهر وڃڻ / ورزش",
      sensitive: "ٻار، بزرگ ۽ دم جا مريض",
      windows: "گهر جون دريون",
    },
    tomTitle: "سڀاڻي جي AI اڳڪٿي",
    tomTag: "Random Forest ML",
    todayAqi: "اڄ جو اندازو",
    tomAqi: "سڀاڻي جو متوقع AQI",
    tomTemp: "سڀاڻي جو گرمي پد",
    tomRain: "سڀاڻي برسات",
    tomGain: (g) => `ماڊل بهتري: +${g}%`,
    noTom: "هن علائقي لاءِ سڀاڻي جي AI اڳڪٿي موجود ناهي — مٿي 24 ڪلاڪن جي پٽي ڏسو.",
    stripTitle: "ايندڙ 24 ڪلاڪن جي هوا ۽ موسم",
    now: "هاڻي",
    sensorsTitle: "ويجها لائيو سينسرز (OpenAQ)",
    noSensors: "ويجهو ڪو گرائونڊ سينسر نه مليو، تنهنڪري AI/سيٽلائيٽ ڊيٽا ڏيکاريو پيو وڃي.",
    kmAway: "ڪلوميٽر پري",
    hrsAgo: "ڪلاڪ اڳ",
    rankTitle: "سنڌ جي 20 شهرن جي تازي رينڪنگ",
    rankSub: "سڀ کان صاف هوا مٿي آهي — تفصيل لاءِ ڪنهن به شهر تي ڪلڪ ڪريو",
    trendsTitle: "هوا جي معيار جو لاڙو",
    selectCity: "شهر چونڊيو:",
    cleanest24: "گذريل 24 ڪلاڪن ۾ سڀ کان صاف وقت",
    peak24: "گذريل 24 ڪلاڪن ۾ سڀ کان وڌيڪ گدلاڻ",
    chart72: "گذريل 72 ڪلاڪن جو AQI گراف",
    chart30: "گذريل 30 ڏينهن جو روزانو اوسط AQI",
    aboutTitle: "سنڌ ايئر واچ بابت",
    aboutSub: "سنڌ جي شهرين لاءِ تيز، سادي ۽ قابلِ اعتماد فضائي گدلاڻ جي مانيٽرنگ",
    aboutMissionTitle: "هي ايپ ڇو ٺاهي وئي؟",
    aboutMissionText:
      "سنڌ ايئر واچ جو مقصد سنڌ جي هر شهر ۽ علائقي جي ماڻهن کي اردو، سنڌي، رومن اردو ۽ انگريزي ۾ هوا جو معيار ۽ سڀاڻي جي AI اڳڪٿي آسانيءَ سان فراهم ڪرڻ آهي.",
    aboutDataTitle: "ڊيٽا ۽ AI ماڊلز",
    aboutDataPoints: [
      "OpenAQ لائيو گرائونڊ سينسرز (جتي موجود هجن)",
      "Open-Meteo سيٽلائيٽ ۽ موسم جو لائيو ڊيٽا",
      "سنڌ جي 20 شهرن لاءِ مقامي Random Forest ML ماڊلز",
      "US EPA معيار موجب PM2.5 مان AQI حساب",
    ],
    aboutAccessTitle: "سڀني لاءِ آسان استعمال",
    aboutAccessPoints: [
      "هڪ ڪلڪ ۾ سنڌ جي وڏن شهرن جي چونڊ",
      "GPS ذريعي ويجھي شهر جي خودڪار سڃاڻپ",
      "چئن ٻولين (اردو، سنڌي، رومن اردو، انگريزي) ۾ مڪمل سهولت",
    ],
    scaleTitle: "US AQI رنگن جو چارٽ",
    loading: "ڊيٽا لوڊ ٿي رهيو آهي...",
    notFound: "هي هنڌ سنڌ ۾ نه مليو. هيٺ ڏنل تجويزون آزمايو:",
    apiErr: "بيڪ اينڊ سرور سان رابطو نه ٿي سگهيو. چيڪ ڪريو ته Python وارو CMD کليل آهي.",
    gpsErr: "لوڪيشن حاصل نه ٿي سگهي، مهرباني ڪري شهر پاڻ چونڊيو.",
    footer: "Sindh AirWatch • Open-Meteo + OpenAQ + مقامي Random Forest ML ماڊلز",
    cats: {
      good: {
        label: "بهترين (صاف هوا)",
        summary: "هوا بلڪل صاف آهي — ٻاهرين سڀني سرگرمين لاءِ محفوظ آهي.",
        cards: {
          mask: "ماسڪ پائڻ جي ڪا ضرورت ناهي.",
          outdoor: "گهمڻ، ڊوڙڻ ۽ راندين لاءِ بهترين وقت آهي.",
          sensitive: "ٻارن، بزرگن ۽ ساهه جي مريضن لاءِ مڪمل محفوظ.",
          windows: "تازي هوا لاءِ گهر جون دريون کليل رکو.",
        },
      },
      mod: {
        label: "مناسب",
        summary: "عام ماڻهن لاءِ هوا ٺيڪ آهي، حساس ماڻهو ٿورو احتياط ڪن.",
        cards: {
          mask: "عام ماڻهن کي ضرورت ناهي؛ مٽي واري روڊ تي هلڪو ماسڪ مفيد آهي.",
          outdoor: "ٻاهر وڃي سگهجي ٿو، پر تمام گهڻي سخت ورزش گهٽ ڪريو.",
          sensitive: "دم يا الرجي جا مريض ٻاهر گهڻو وقت نه گذارين.",
          windows: "صبح ۽ شام جي وقت دريون کولي سگهجن ٿيون.",
        },
      },
      usg: {
        label: "حساس ماڻهن لاءِ نقصانڪار",
        summary: "ٻارن، بزرگن ۽ ساهه جي مريضن کي احتياط ڪرڻ گهرجي.",
        cards: {
          mask: "حساس ماڻهو ۽ موٽرسائيڪل سوار ٻاهر ماسڪ ضرور پائين.",
          outdoor: "ٻاهر گهڻي محنت واري ورزش ۽ راند گهٽ ڪريو.",
          sensitive: "ٻار، بزرگ ۽ دم جا مريض گهر اندر رهن ۽ دوا ساڻ رکن.",
          windows: "مٽي ۽ دونهي کان بچڻ لاءِ دريون گهڻو ڪري بند رکو.",
        },
      },
      unh: {
        label: "غير صحت بخش",
        summary: "هوا گدلي آهي — هر ڪنهن کي ٻاهر نڪرندي احتياط ڪرڻ گهرجي.",
        cards: {
          mask: "ٻاهر نڪرندي N95 يا KN95 ماسڪ لازمي پائيندا ڪريو.",
          outdoor: "ٻاهرين ورزش ۽ بنا ضرورت گهمڻ ملتوي ڪريو.",
          sensitive: "ٻارن، بزرگن ۽ دل يا ساهه جي مريضن کي گهر اندر رکو.",
          windows: "دريون ۽ دروازا چڱيءَ طرح بند رکو.",
        },
      },
      vunh: {
        label: "انتهائي غير صحت بخش",
        summary: "هوا سخت گدلي آهي — بنا ضرورت گهر کان ٻاهر نه نڪرو.",
        cards: {
          mask: "مجبوريءَ ۾ ٻاهر نڪرڻو پوي ته فٽ N95 ماسڪ پائيندا ڪريو.",
          outdoor: "هر قسم جي ٻاهرين سرگرمي ۽ راند مڪمل بند رکو.",
          sensitive: "ٻارن، بزرگن ۽ مريضن جو خاص خيال رکو ۽ ٻاهر نه موڪليو.",
          windows: "دريون مڪمل بند رکو ۽ ممڪن هجي ته ايئر پيوريفائر هلايو.",
        },
      },
      haz: {
        label: "خطرناڪ",
        summary: "هنگامي صورتحال: فضا خطرناڪ حد تائين گدلي آهي.",
        cards: {
          mask: "ضروري نڪرڻ جي صورت ۾ رڳو N95/P100 ماسڪ پائيندا ڪريو.",
          outdoor: "ٻاهر نڪرڻ مڪمل طور تي بند ڪريو.",
          sensitive: "ساهه ۾ تڪليف هجي ته فوري ڊاڪٽر سان رابطو ڪريو.",
          windows: "سڀ دريون ۽ دروازا چڱي ريت بند رکو.",
        },
      },
    },
  },
  ru: {
    rtl: false,
    brand: "Sindh AirWatch",
    sub: "Sindh bhar ki live hawa aur AI forecast",
    placeholder: "Sindh ka koi shehar ya ilaqa likhein (jaise Karachi, Clifton, Nawabshah)...",
    search: "Search",
    gps: "📍 Meri Location",
    quickLabel: "1-click mein apna shehar chunein:",
    tabLive: "Live & Forecast",
    tabRank: "Sindh Ranking (20 Cities)",
    tabTrends: "Historical Trends",
    tabAbout: "About",
    updated: "Updated",
    groundSrc: (n) => `Live Ground Sensors (${n})`,
    modelSrc: "Satellite + AI Model",
    sky: {
      clearDay: "Saaf Dhoop",
      clearNight: "Saaf Raat",
      partly: "Halke Badal",
      cloudy: "Badal Chhaye Hue",
      fog: "Dhund / Smog",
      rain: "Barish",
      storm: "Aandhi aur Garaj",
    },
    temp: "Temperature",
    feels: "Feels Like",
    hum: "Humidity",
    wind: "Hawa (Wind)",
    rain: "Barish Chance",
    adviceTitle: "Sehat ke liye Alag Alag Hidayat",
    adviceSub: "Mojooda hawa ke hisab se ehtiyati tadabeer",
    adviceLabels: {
      mask: "Mask",
      outdoor: "Bahar Jana / Exercise",
      sensitive: "Bachay, Buzurg & Asthma",
      windows: "Ghar ki Khirkiyan",
    },
    tomTitle: "Kal ki AI Forecast",
    tomTag: "Random Forest ML",
    todayAqi: "Aaj ka Estimate",
    tomAqi: "Kal ka Expected AQI",
    tomTemp: "Kal ka Mausam",
    tomRain: "Kal Barish",
    tomGain: (g) => `Model Behtari: +${g}%`,
    noTom: "Is ilaqay ke liye kal ki AI forecast abhi available nahi — upar 24 ghante ki strip dekhein.",
    stripTitle: "Agle 24 Ghanton ki Hawa aur Mausam",
    now: "Abhi",
    sensorsTitle: "Qareebi Live Sensors (OpenAQ)",
    noSensors: "Is ilaqay ke qareeb koi active ground sensor nahi mila, is liye AI/satellite data dikhaya ja raha hai.",
    kmAway: "km door",
    hrsAgo: "ghante pehle",
    rankTitle: "Sindh ke 20 Shehron ki Taza Ranking",
    rankSub: "Sab se saaf hawa upar hai — detail dekhne ke liye kisi bhi shehar par click karein",
    trendsTitle: "Hawa ke Mayaar ka Trend",
    selectCity: "Shehar chunein:",
    cleanest24: "Pichhle 24 ghante mein sab se saaf waqt",
    peak24: "Pichhle 24 ghante mein sab se zyada aaloodgi",
    chart72: "Pichhle 72 Ghanton ka AQI Graph",
    chart30: "Pichhle 30 Dinon ka Daily Average AQI",
    aboutTitle: "Sindh AirWatch ke Baray Mein",
    aboutSub: "Sindh ke logon ke liye tez, aasan aur qabil-e-aitemaad AQI monitoring",
    aboutMissionTitle: "Yeh App Kyun Banayi Gayi?",
    aboutMissionText:
      "Sindh AirWatch ka maqsad Sindh ke har shehar aur ilaqay ke logon ko Urdu, Sindhi, Roman Urdu aur English mein live hawa ka haal aur kal ki AI forecast aasani se dena hai taake har koi apni sehat ka khayal rakh sake.",
    aboutDataTitle: "Data aur AI Models",
    aboutDataPoints: [
      "OpenAQ live ground sensors (jahan available hon)",
      "Open-Meteo satellite aur live mausam ka data",
      "Sindh ke 20 shehron ke liye local Random Forest ML models",
      "US EPA standard ke mutabiq PM2.5 se AQI calculation",
    ],
    aboutAccessTitle: "Sab ke liye Aasan Istemal",
    aboutAccessPoints: [
      "1-click mein Sindh ke baray shehron ka intekhab",
      "GPS ke zariye qareebi shehar ki khud-ba-khud pehchan",
      "4 zubanon (Urdu, Sindhi, Roman Urdu, English) mein mukammal sahulat",
    ],
    scaleTitle: "US AQI Rangon ka Chart",
    loading: "Data load ho raha hai...",
    notFound: "Yeh jagah Sindh mein nahi mili. Neeche diye gaye options try karein:",
    apiErr: "Backend server se rabta nahi ho saka. Check karein ke Python wala CMD khula hua hai.",
    gpsErr: "Location nahi mil saki, please apna shehar khud select karein.",
    footer: "Sindh AirWatch • Open-Meteo + OpenAQ + Local Random Forest ML Models",
    cats: {
      good: {
        label: "Behtareen (Saaf Hawa)",
        summary: "Hawa bilkul saaf hai — bahar ki tamam activities mehfooz hain.",
        cards: {
          mask: "Mask pehne ki koi zaroorat nahi.",
          outdoor: "Walk, running aur sports ke liye behtareen waqt hai.",
          sensitive: "Bachon, buzurgon aur asthma ke mareezon ke liye bilkul safe.",
          windows: "Taza hawa ke liye ghar ki khirkiyan khuli rakhein.",
        },
      },
      mod: {
        label: "Munasib",
        summary: "Aam logon ke liye hawa theek hai, hassas afraad halka ehtiyat karein.",
        cards: {
          mask: "Aam logon ko zaroorat nahi; dhool wali sarak par halka mask behtar hai.",
          outdoor: "Bahar ja sakte hain, magar bohat zyada sakht exercise kam rakhein.",
          sensitive: "Asthma ya allergy ke mareez bahar zyada dair rehne mein ehtiyat karein.",
          windows: "Subah aur shaam ke waqt khirkiyan kholi ja sakti hain.",
        },
      },
      usg: {
        label: "Hassas Afraad ke liye Nuqsan-deh",
        summary: "Bachon, buzurgon aur saans ke mareezon ko ehtiyat ki zaroorat hai.",
        cards: {
          mask: "Hassas afraad aur bike sawar bahar mask zaroor pehnein.",
          outdoor: "Bahar zyada mehnat wali exercise aur sports kam karein.",
          sensitive: "Bachay, buzurg aur asthma mareez inhaler saath rakhein aur andar rahein.",
          windows: "Mitti aur dhuen se bachne ke liye khirkiyan zyada tar band rakhein.",
        },
      },
      unh: {
        label: "Ghair Sehat-bakhsh",
        summary: "Hawa aalooda hai — har shakhs ko bahar nikaltay waqt ehtiyat karni chahiye.",
        cards: {
          mask: "Bahar nikaltay waqt N95 ya KN95 mask lazmi pehnein.",
          outdoor: "Bahar ki exercise aur ghair zaroori walk multawi kar dein.",
          sensitive: "Bachon, buzurgon aur dil/saans ke mareezon ko ghar ke andar rakhein.",
          windows: "Khirkiyan aur darwazay achi tarah band rakhein.",
        },
      },
      vunh: {
        label: "Bohat Ghair Sehat-bakhsh",
        summary: "Hawa shadeed aalooda hai — ghair zaroori ghar se bahar na niklein.",
        cards: {
          mask: "Majboori mein bahar jana paray toh fit N95 mask pehnein.",
          outdoor: "Har qisam ki outdoor activity aur sports mukammal band rakhein.",
          sensitive: "Bachon, buzurgon aur mareezon ka khaas khayal rakhein aur bahar na bhejein.",
          windows: "Khirkiyan mukammal band rakhein aur mumkin ho toh air purifier chalayein.",
        },
      },
      haz: {
        label: "Khatarnak",
        summary: "Emergency alert: Hawa khatarnak had tak aalooda hai.",
        cards: {
          mask: "Zaroori nikalna paray toh sirf N95/P100 mask pehnein.",
          outdoor: "Bahar nikalna mukammal band kar dein.",
          sensitive: "Saans mein takleef ho toh fori doctor se rujoo karein.",
          windows: "Tamam khirkiyan aur darwazay seal band rakhein.",
        },
      },
    },
  },
  en: {
    rtl: false,
    brand: "Sindh AirWatch",
    sub: "Real-time Sindh Air Quality & AI Forecasting",
    placeholder: "Search any city or area in Sindh (e.g., Karachi, Clifton, Nawabshah)...",
    search: "Search",
    gps: "📍 My Location",
    quickLabel: "Quick 1-click city selection:",
    tabLive: "Live & Forecast",
    tabRank: "Sindh Ranking (20 Cities)",
    tabTrends: "Trends",
    tabAbout: "About",
    updated: "Updated",
    groundSrc: (n) => `Live Ground Sensors (${n})`,
    modelSrc: "Satellite + AI Model",
    sky: {
      clearDay: "Clear Sunny",
      clearNight: "Clear Night",
      partly: "Partly Cloudy",
      cloudy: "Cloudy",
      fog: "Hazy / Foggy",
      rain: "Rainy",
      storm: "Thunderstorm",
    },
    temp: "Temperature",
    feels: "Feels Like",
    hum: "Humidity",
    wind: "Wind Speed",
    rain: "Rain Chance",
    adviceTitle: "Actionable Health Advice",
    adviceSub: "Separate precautions based on current air quality",
    adviceLabels: {
      mask: "Mask",
      outdoor: "Outdoor & Exercise",
      sensitive: "Kids, Elderly & Asthma",
      windows: "Home Windows",
    },
    tomTitle: "Tomorrow's AI Forecast",
    tomTag: "Random Forest ML",
    todayAqi: "Today's Estimate",
    tomAqi: "Predicted Tomorrow AQI",
    tomTemp: "Tomorrow's Temp",
    tomRain: "Rain Chance",
    tomGain: (g) => `Model Gain: +${g}%`,
    noTom: "No ML tomorrow forecast for this area yet — check the 24-hour strip above.",
    stripTitle: "Next 24 Hours Air & Weather",
    now: "Now",
    sensorsTitle: "Nearby Live Sensors (OpenAQ)",
    noSensors: "No active ground sensor found nearby, showing Satellite + AI estimate.",
    kmAway: "km away",
    hrsAgo: "hrs ago",
    rankTitle: "Live Ranking of 20 Sindh Cities",
    rankSub: "Cleanest air at the top — click any city to inspect details",
    trendsTitle: "Historical Air Quality Trends",
    selectCity: "Select City:",
    cleanest24: "Cleanest Hour (Last 24h)",
    peak24: "Peak Pollution (Last 24h)",
    chart72: "Last 72 Hours AQI Trend",
    chart30: "Last 30 Days Daily Average AQI",
    aboutTitle: "About Sindh AirWatch",
    aboutSub: "Fast, accessible air quality monitoring & ML forecasting built for Sindh",
    aboutMissionTitle: "Why Sindh AirWatch?",
    aboutMissionText:
      "Sindh AirWatch brings real-time air quality monitoring and next-day AI forecasting to every city and town in Sindh in Urdu, Sindhi, Roman Urdu, and English so families can protect their health every day.",
    aboutDataTitle: "Data & AI Pipeline",
    aboutDataPoints: [
      "OpenAQ live ground-level monitoring sensors (where available)",
      "Open-Meteo real-time satellite air quality and weather feeds",
      "Custom local Random Forest ML models trained across 20 Sindh cities",
      "US EPA standard PM2.5 to AQI conversion",
    ],
    aboutAccessTitle: "Built for Everyone",
    aboutAccessPoints: [
      "1-click city buttons in Urdu, Sindhi, Roman Urdu & English",
      "Automatic nearest-city detection via browser GPS",
      "Clean, responsive React + FastAPI architecture for instant loading",
    ],
    scaleTitle: "US AQI Color Scale",
    loading: "Loading data...",
    notFound: "Place not found in Sindh. Try one of these suggestions:",
    apiErr: "Cannot connect to backend server. Make sure your Python Uvicorn CMD is running.",
    gpsErr: "Could not access GPS location. Please select a city manually.",
    footer: "Sindh AirWatch • Open-Meteo + OpenAQ + Local Random Forest ML Models",
    cats: {
      good: {
        label: "Good",
        summary: "Air quality is clean and safe for all outdoor activities.",
        cards: {
          mask: "No mask needed outdoors.",
          outdoor: "Great time for walking, running, and outdoor sports.",
          sensitive: "Completely safe for children, elderly, and asthma patients.",
          windows: "Keep windows open to let fresh air circulate.",
        },
      },
      mod: {
        label: "Moderate",
        summary: "Acceptable air quality; sensitive people should take light care.",
        cards: {
          mask: "Not required for most; light mask helpful on dusty roads.",
          outdoor: "Safe to go outside; keep intense long workouts moderate.",
          sensitive: "People with asthma or allergies should limit long outdoor exposure.",
          windows: "Safe to ventilate during cooler morning or evening hours.",
        },
      },
      usg: {
        label: "Unhealthy for Sensitive Groups",
        summary: "Children, elderly, and people with asthma should take precautions.",
        cards: {
          mask: "Sensitive individuals and motorcyclists should wear a mask outdoors.",
          outdoor: "Reduce prolonged or heavy outdoor exertion.",
          sensitive: "Children, elderly, and asthma patients should stay indoors with inhalers handy.",
          windows: "Keep windows mostly closed to block dust and smoke.",
        },
      },
      unh: {
        label: "Unhealthy",
        summary: "Polluted air — everyone should limit exposure outdoors.",
        cards: {
          mask: "Wear an N95 or KN95 mask whenever stepping outside.",
          outdoor: "Postpone outdoor workouts and non-essential walks.",
          sensitive: "Keep children, seniors, and heart/lung patients indoors.",
          windows: "Keep windows and doors tightly shut.",
        },
      },
      vunh: {
        label: "Very Unhealthy",
        summary: "Severe air pollution — avoid unnecessary outdoor trips.",
        cards: {
          mask: "If you must go outside, wear a properly fitted N95 mask.",
          outdoor: "Cancel all outdoor activities and physical exertion.",
          sensitive: "Monitor children, seniors, and respiratory patients closely indoors.",
          windows: "Keep all windows closed and run an air purifier if available.",
        },
      },
      haz: {
        label: "Hazardous",
        summary: "Health emergency: air pollution is at dangerous levels.",
        cards: {
          mask: "Use an N95/P100 respirator only if outdoor travel is unavoidable.",
          outdoor: "Avoid going outdoors completely.",
          sensitive: "Seek medical help immediately if breathing feels difficult.",
          windows: "Seal windows and doors to keep polluted air out.",
        },
      },
    },
  },
};

function getAqiMeta(aqi, lang) {
  const cats = TEXT[lang].cats;
  if (aqi <= 50) return { ...cats.good, color: "#22c55e", bar: "#16a34a" };
  if (aqi <= 100) return { ...cats.mod, color: "#facc15", bar: "#ca8a04" };
  if (aqi <= 150) return { ...cats.usg, color: "#fb923c", bar: "#ea580c" };
  if (aqi <= 200) return { ...cats.unh, color: "#f87171", bar: "#dc2626" };
  if (aqi <= 300) return { ...cats.vunh, color: "#c084fc", bar: "#9333ea" };
  return { ...cats.haz, color: "#fb7185", bar: "#881337" };
}

function getPageSkyGradient(aqi, isDay, isRaining) {
  if (!isDay) {
    return "linear-gradient(180deg, #060b19 0%, #0f172a 48%, #1e293b 100%)";
  }
  if (isRaining) {
    return "linear-gradient(180deg, #64748b 0%, #94a3b8 46%, #cbd5e1 100%)";
  }
  if (aqi > 100) {
    return "linear-gradient(180deg, #7dd3fc 0%, #fed7aa 55%, #fef3c7 100%)";
  }
  return "linear-gradient(180deg, #38bdf8 0%, #bae6fd 45%, #e0f2fe 100%)";
}

function getHeroSkyGradient(aqi, isDay, isRaining) {
  if (!isDay) {
    if (aqi <= 50) return "linear-gradient(155deg, #0b132b 0%, #1c2541 55%, #0f766e 100%)";
    if (aqi <= 100) return "linear-gradient(155deg, #0f172a 0%, #1e293b 55%, #854d0e 100%)";
    if (aqi <= 150) return "linear-gradient(155deg, #0f172a 0%, #27272a 52%, #9a3412 100%)";
    if (aqi <= 200) return "linear-gradient(155deg, #0f172a 0%, #2e1020 52%, #991b1b 100%)";
    return "linear-gradient(155deg, #0f172a 0%, #2e1065 55%, #6b21a8 100%)";
  }
  if (isRaining) {
    return "linear-gradient(150deg, #1e3a5f 0%, #334155 55%, #475569 100%)";
  }
  if (aqi <= 50) return "linear-gradient(145deg, #0284c7 0%, #0ea5e9 55%, #14b8a6 100%)";
  if (aqi <= 100) return "linear-gradient(145deg, #0369a1 0%, #0d9488 52%, #ca8a04 100%)";
  if (aqi <= 150) return "linear-gradient(145deg, #1e3a5f 0%, #b45309 55%, #ea580c 100%)";
  if (aqi <= 200) return "linear-gradient(145deg, #3b1d2e 0%, #991b1b 55%, #dc2626 100%)";
  if (aqi <= 300) return "linear-gradient(145deg, #1e1b4b 0%, #581c87 55%, #9333ea 100%)";
  return "linear-gradient(145deg, #1f0a14 0%, #4c0519 55%, #881337 100%)";
}

function weatherIcon(code, isDay) {
  if (code === 0) return isDay ? "☀️" : "🌙";
  if (code === 1 || code === 2) return isDay ? "🌤️" : "☁️";
  if (code === 3) return "☁️";
  if (code === 45 || code === 48) return "🌫️";
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return "🌧️";
  if (code >= 95) return "⛈️";
  return isDay ? "⛅" : "🌙";
}

function getSkyLabel(code, isDay, aqi, lang) {
  const s = TEXT[lang].sky;
  if (code >= 95) return s.storm;
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return s.rain;
  if (code === 45 || code === 48 || aqi >= 160) return s.fog;
  if (code === 3) return s.cloudy;
  if (code === 1 || code === 2) return s.partly;
  return isDay ? s.clearDay : s.clearNight;
}

function AqiGauge({ aqi, pm25, color }) {
  const r = 68;
  const arcLen = Math.PI * r;
  const pct = Math.min(1, Math.max(0.05, aqi / 300));
  const offset = arcLen * (1 - pct);
  const theta = Math.PI * (1 - pct);
  const dotX = 90 + r * Math.cos(theta);
  const dotY = 92 - r * Math.sin(theta);

  return (
    <div className="aqi-gauge-box" dir="ltr">
      <svg viewBox="0 0 180 108" className="gauge-svg">
        <path
          d="M 22 92 A 68 68 0 0 1 158 92"
          fill="none"
          stroke="rgba(255,255,255,0.22)"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d="M 22 92 A 68 68 0 0 1 158 92"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={arcLen}
          strokeDashoffset={offset}
        />
        <circle
          cx={dotX}
          cy={dotY}
          r="6.5"
          fill="#ffffff"
          stroke={color}
          strokeWidth="3.5"
        />
        <text x="90" y="48" textAnchor="middle" fill="rgba(255,255,255,0.85)" fontSize="11" fontWeight="700">
          US AQI
        </text>
        <text x="90" y="84" textAnchor="middle" fill="#ffffff" fontSize="36" fontWeight="800">
          {aqi}
        </text>
      </svg>
      <div className="gauge-pm">PM2.5: {pm25} µg/m³</div>
    </div>
  );
}

function SimpleLineChart({ data, valueKey, labelKey, stroke = "#0f766e" }) {
  if (!data || data.length < 2) return null;
  const W = 640;
  const H = 200;
  const pad = 28;
  const vals = data.map((d) => d[valueKey]);
  const minV = Math.max(0, Math.floor(Math.min(...vals) - 10));
  const maxV = Math.ceil(Math.max(...vals) + 10);
  const span = Math.max(1, maxV - minV);

  const pts = data.map((d, i) => {
    const x = pad + (i / (data.length - 1)) * (W - pad * 2);
    const y = H - pad - ((d[valueKey] - minV) / span) * (H - pad * 2);
    return { x, y };
  });

  const linePath = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${pts[pts.length - 1].x.toFixed(1)},${H - pad} L${pts[0].x.toFixed(1)},${H - pad} Z`;

  return (
    <div className="chart-box">
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg">
        <line x1={pad} y1={pad} x2={W - pad} y2={pad} stroke="rgba(148,163,184,0.28)" strokeDasharray="4" />
        <line x1={pad} y1={H / 2} x2={W - pad} y2={H / 2} stroke="rgba(148,163,184,0.28)" strokeDasharray="4" />
        <line x1={pad} y1={H - pad} x2={W - pad} y2={H - pad} stroke="rgba(148,163,184,0.4)" />
        <text x={4} y={pad + 4} fontSize="11" fill="#94a3b8">{maxV}</text>
        <text x={4} y={H / 2 + 4} fontSize="11" fill="#94a3b8">{Math.round((minV + maxV) / 2)}</text>
        <text x={4} y={H - pad + 4} fontSize="11" fill="#94a3b8">{minV}</text>
        <path d={areaPath} fill={stroke} fillOpacity="0.16" />
        <path d={linePath} fill="none" stroke={stroke} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="chart-footer" dir="ltr">
        <span>{data[0][labelKey]}</span>
        <span>{data[Math.floor(data.length / 2)][labelKey]}</span>
        <span>{data[data.length - 1][labelKey]}</span>
      </div>
    </div>
  );
}

export default function App() {
  const [lang, setLang] = useState("ur");
  const [tab, setTab] = useState("live");
  const [query, setQuery] = useState("Karachi");
  const [activeCity, setActiveCity] = useState("Karachi");

  const [placeData, setPlaceData] = useState(null);
  const [loadingPlace, setLoadingPlace] = useState(true);
  const [placeErr, setPlaceErr] = useState("");

  const [ranking, setRanking] = useState([]);
  const [loadingRank, setLoadingRank] = useState(false);

  const [trendCity, setTrendCity] = useState("Karachi");
  const [trendData, setTrendData] = useState(null);
  const [loadingTrend, setLoadingTrend] = useState(false);

  const t = TEXT[lang];

  const cur = placeData?.current;
  const heroMeta = cur ? getAqiMeta(cur.aqi, lang) : null;
  const tom = placeData?.tomorrow;
  const nowHour =
    placeData?.hourly_24h?.find((h) => h.is_now) || placeData?.hourly_24h?.[0] || null;
  const isDay = nowHour ? nowHour.is_day === 1 : true;
  const wCode = nowHour ? nowHour.weather_code : 0;
  const isRaining =
    (wCode >= 51 && wCode <= 67) ||
    (wCode >= 80 && wCode <= 82) ||
    wCode >= 95 ||
    (cur?.rain ?? 0) >= 60;
  const isHazy = (cur?.aqi ?? 0) > 100;

  useEffect(() => {
    document.documentElement.dir = t.rtl ? "rtl" : "ltr";
    document.documentElement.lang = lang === "ru" ? "en" : lang;
    document.body.classList.toggle("rtl", t.rtl);
  }, [lang, t.rtl]);

  useEffect(() => {
    document.body.classList.toggle("sky-dark", !isDay);
    document.documentElement.style.setProperty(
      "--sky-bg",
      getPageSkyGradient(cur?.aqi ?? 50, isDay, isRaining)
    );
  }, [cur?.aqi, isDay, isRaining]);

  async function loadPlace(qText) {
    setLoadingPlace(true);
    setPlaceErr("");
    try {
      const res = await fetch(`${API_BASE}/api/place?q=${encodeURIComponent(qText)}`);
      if (!res.ok) throw new Error("API error");
      const json = await res.json();
      setPlaceData(json);
      if (json.found && json.place?.name) {
        setActiveCity(json.place.name);
      }
    } catch {
      setPlaceErr(t.apiErr);
    } finally {
      setLoadingPlace(false);
    }
  }

  async function loadRanking() {
    if (ranking.length > 0) return;
    setLoadingRank(true);
    try {
      const res = await fetch(`${API_BASE}/api/ranking`);
      const json = await res.json();
      setRanking(json.rows || []);
    } catch {
      setRanking([]);
    } finally {
      setLoadingRank(false);
    }
  }

  async function loadTrends(cityName) {
    setLoadingTrend(true);
    try {
      const res = await fetch(`${API_BASE}/api/trends?city=${encodeURIComponent(cityName)}`);
      const json = await res.json();
      setTrendData(json);
    } catch {
      setTrendData(null);
    } finally {
      setLoadingTrend(false);
    }
  }

  useEffect(() => {
    loadPlace("Karachi");
  }, []);

  useEffect(() => {
    if (tab === "ranking") loadRanking();
    if (tab === "trends") loadTrends(trendCity);
  }, [tab, trendCity]);

  function handleSearch(e) {
    e.preventDefault();
    const cleaned = query.trim();
    if (!cleaned) return;
    setTab("live");
    loadPlace(cleaned);
  }

  function pickCity(cityKey) {
    setQuery(cityKey);
    setActiveCity(cityKey);
    setTab("live");
    loadPlace(cityKey);
  }

  function handleGPS() {
    if (!navigator.geolocation) {
      setPlaceErr(t.gpsErr);
      return;
    }
    setLoadingPlace(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords;
          const res = await fetch(`${API_BASE}/api/nearest?lat=${latitude}&lon=${longitude}`);
          const json = await res.json();
          const city = json.city || "Karachi";
          setQuery(city);
          setActiveCity(city);
          setTab("live");
          loadPlace(city);
        } catch {
          setLoadingPlace(false);
          setPlaceErr(t.gpsErr);
        }
      },
      () => {
        setLoadingPlace(false);
        setPlaceErr(t.gpsErr);
      }
    );
  }

  return (
    <>
      {/* Full-Screen Live Ambient Sky */}
      <div className="global-sky" aria-hidden="true">
        {!isDay &&
          GLOBAL_STARS.map((st, idx) => (
            <span
              key={idx}
              className="star"
              style={{ top: st.top, left: st.left, animationDelay: st.delay }}
            />
          ))}
        <div className="global-cloud g-cloud-1" />
        <div className="global-cloud g-cloud-2" />
        <div className="global-cloud g-cloud-3" />
      </div>

      <div className="app-shell">
        {/* Topbar */}
        <header className="topbar">
          <div className="brand">
            <div className="brand-dot">{weatherIcon(wCode, isDay)}</div>
            <div>
              <div className="brand-title">{t.brand}</div>
              <div className="brand-sub">{t.sub}</div>
            </div>
          </div>
          <div className="lang-switcher">
            {[
              { code: "ur", label: "اردو" },
              { code: "sd", label: "سنڌي" },
              { code: "ru", label: "Roman Urdu" },
              { code: "en", label: "English" },
            ].map((item) => (
              <button
                key={item.code}
                className={`lang-btn ${lang === item.code ? "active" : ""}`}
                onClick={() => setLang(item.code)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </header>

        {/* Search + 1-Click Cities */}
        <section className="search-card">
          <form className="search-row" onSubmit={handleSearch}>
            <input
              className="search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t.placeholder}
            />
            <button type="submit" className="btn-primary">{t.search}</button>
            <button type="button" className="btn-gps" onClick={handleGPS}>{t.gps}</button>
          </form>

          <div className="quick-cities-label">{t.quickLabel}</div>
          <div className="city-pills">
            {QUICK_CITIES.map((c) => (
              <button
                key={c.key}
                type="button"
                className={`city-pill ${activeCity.toLowerCase() === c.key.toLowerCase() ? "active" : ""}`}
                onClick={() => pickCity(c.key)}
              >
                {c[lang]}
              </button>
            ))}
          </div>
        </section>

        {/* Tabs */}
        <nav className="tabs-bar">
          <button className={`tab-btn ${tab === "live" ? "active" : ""}`} onClick={() => setTab("live")}>
            {t.tabLive}
          </button>
          <button className={`tab-btn ${tab === "ranking" ? "active" : ""}`} onClick={() => setTab("ranking")}>
            {t.tabRank}
          </button>
          <button className={`tab-btn ${tab === "trends" ? "active" : ""}`} onClick={() => setTab("trends")}>
            {t.tabTrends}
          </button>
          <button className={`tab-btn ${tab === "about" ? "active" : ""}`} onClick={() => setTab("about")}>
            {t.tabAbout}
          </button>
        </nav>

        {/* TAB 1: LIVE & FORECAST */}
        {tab === "live" && (
          <>
            {placeErr && <div className="error-box">{placeErr}</div>}

            {loadingPlace && (
              <div className="loader-box">
                <div className="spinner" />
                <div>{t.loading}</div>
              </div>
            )}

            {!loadingPlace && !placeErr && placeData && !placeData.found && (
              <div className="empty-box">
                <div>{t.notFound}</div>
                <div className="suggest-row" style={{ justifyContent: "center" }}>
                  {(placeData.suggestions || []).map((s) => (
                    <button key={s} className="suggest-chip" onClick={() => pickCity(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {!loadingPlace && !placeErr && placeData?.found && cur && heroMeta && (
              <>
                {/* Live Animated Weather + AQI Hero Card */}
                <section
                  className="hero-card"
                  style={{ background: getHeroSkyGradient(cur.aqi, isDay, isRaining) }}
                >
                  {/* Animated Sky Scene Layer */}
                  <div className="sky-scene" aria-hidden="true">
                    {isDay ? (
                      <div className="sun-orb" />
                    ) : (
                      <>
                        <div className="moon-orb" />
                        {STARS.map((st, idx) => (
                          <span
                            key={idx}
                            className="star"
                            style={{ top: st.top, left: st.left, animationDelay: st.delay }}
                          />
                        ))}
                      </>
                    )}
                    <div className="cloud cloud-1" />
                    <div className="cloud cloud-2" />
                    <div className="cloud cloud-3" />
                    {isHazy && <div className="haze-layer" />}
                    {isRaining &&
                      RAIN_DROPS.map((rd, idx) => (
                        <span
                          key={idx}
                          className="rain-drop"
                          style={{ left: rd.left, animationDelay: rd.delay }}
                        />
                      ))}
                  </div>

                  {/* Foreground Weather + Gauge Content */}
                  <div className="hero-content">
                    <div className="hero-top">
                      <div>
                        <div className="place-name">{placeData.place.name}</div>
                        <div className="place-meta">
                          {placeData.place.district} • {t.updated}: {placeData.stamp}
                        </div>
                      </div>
                      <div className="hero-badges">
                        <span className="sky-badge">
                          {weatherIcon(wCode, isDay)} {getSkyLabel(wCode, isDay, cur.aqi, lang)}
                        </span>
                        <span className="source-badge">
                          {cur.source_type === "ground"
                            ? t.groundSrc(cur.sensor_count)
                            : t.modelSrc}
                        </span>
                      </div>
                    </div>

                    <div className="hero-main">
                      <AqiGauge aqi={cur.aqi} pm25={cur.pm25} color={heroMeta.color} />
                      <div>
                        <div className="aqi-cat-row">
                          <div className="aqi-cat">{heroMeta.label}</div>
                          {cur.temp !== null && (
                            <span className="hero-temp-pill">
                              {weatherIcon(wCode, isDay)} {cur.temp}°C
                            </span>
                          )}
                        </div>
                        <div className="advice-box">{heroMeta.summary}</div>
                      </div>
                    </div>

                    <div className="weather-grid">
                      <div className="wx-item">
                        <div className="wx-head">
                          <span className="wx-icon">🌡️</span>
                          <span className="wx-label">{t.temp}</span>
                        </div>
                        <div className="wx-val">{cur.temp !== null ? `${cur.temp}°C` : "--"}</div>
                      </div>
                      <div className="wx-item">
                        <div className="wx-head">
                          <span className="wx-icon">🌤️</span>
                          <span className="wx-label">{t.feels}</span>
                        </div>
                        <div className="wx-val">{cur.feels !== null ? `${cur.feels}°C` : "--"}</div>
                      </div>
                      <div className="wx-item">
                        <div className="wx-head">
                          <span className="wx-icon">💧</span>
                          <span className="wx-label">{t.hum}</span>
                        </div>
                        <div className="wx-val">{cur.hum !== null ? `${cur.hum}%` : "--"}</div>
                      </div>
                      <div className="wx-item">
                        <div className="wx-head">
                          <span className="wx-icon">💨</span>
                          <span className="wx-label">{t.wind}</span>
                        </div>
                        <div className="wx-val">{cur.wind !== null ? `${cur.wind} km/h` : "--"}</div>
                      </div>
                      <div className="wx-item">
                        <div className="wx-head">
                          <span className="wx-icon">🌧️</span>
                          <span className="wx-label">{t.rain}</span>
                        </div>
                        <div className="wx-val">{cur.rain !== null ? `${cur.rain}%` : "--"}</div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Separate Health Advice Cards */}
                <section className="card">
                  <div className="card-header">
                    <div>
                      <div className="card-title">{t.adviceTitle}</div>
                      <div className="card-sub">{t.adviceSub}</div>
                    </div>
                  </div>
                  <div className="advice-grid">
                    <div className="advice-card">
                      <div className="advice-icon">😷</div>
                      <div>
                        <div className="advice-card-title">{t.adviceLabels.mask}</div>
                        <div className="advice-card-text">{heroMeta.cards.mask}</div>
                      </div>
                    </div>
                    <div className="advice-card">
                      <div className="advice-icon">🏃</div>
                      <div>
                        <div className="advice-card-title">{t.adviceLabels.outdoor}</div>
                        <div className="advice-card-text">{heroMeta.cards.outdoor}</div>
                      </div>
                    </div>
                    <div className="advice-card">
                      <div className="advice-icon">👶</div>
                      <div>
                        <div className="advice-card-title">{t.adviceLabels.sensitive}</div>
                        <div className="advice-card-text">{heroMeta.cards.sensitive}</div>
                      </div>
                    </div>
                    <div className="advice-card">
                      <div className="advice-icon">🪟</div>
                      <div>
                        <div className="advice-card-title">{t.adviceLabels.windows}</div>
                        <div className="advice-card-text">{heroMeta.cards.windows}</div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Tomorrow AI Forecast */}
                <section className="card">
                  <div className="card-header">
                    <div>
                      <div className="card-title">{t.tomTitle}</div>
                      {typeof tom?.gain === "number" && (
                        <div className="card-sub">{t.tomGain(tom.gain)}</div>
                      )}
                    </div>
                    {tom && <span className="ml-tag">{t.tomTag}</span>}
                  </div>

                  {tom ? (
                    <div className="tom-grid">
                      <div className="tom-box">
                        <div className="tom-meta">{t.tomAqi}</div>
                        <div
                          className="tom-aqi"
                          style={{ color: getAqiMeta(tom.tomorrow_aqi, lang).bar }}
                        >
                          {tom.tomorrow_aqi}
                        </div>
                        <div className="tom-meta">
                          {getAqiMeta(tom.tomorrow_aqi, lang).label}
                        </div>
                      </div>

                      <div className="tom-box">
                        <div className="tom-meta">{t.todayAqi}</div>
                        <div
                          className="tom-aqi"
                          style={{ color: getAqiMeta(tom.today_aqi, lang).bar }}
                        >
                          {tom.today_aqi}
                        </div>
                        <div className="tom-meta">{tom.city}</div>
                      </div>

                      <div className="tom-box">
                        <div className="tom-meta">{t.tomTemp}</div>
                        <div className="tom-aqi" style={{ fontSize: "1.45rem" }}>
                          {tom.temp_max}° / {tom.temp_min}°C
                        </div>
                        <div className="tom-meta">
                          {t.tomRain}: {tom.rain ?? 0}%
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="card-sub">{t.noTom}</div>
                  )}
                </section>

                {/* 24-Hour Strip */}
                {placeData.hourly_24h?.length > 0 && (
                  <section className="card">
                    <div className="card-header">
                      <div className="card-title">{t.stripTitle}</div>
                    </div>
                    <div className="strip-scroll">
                      {placeData.hourly_24h.map((h, i) => {
                        const meta = getAqiMeta(h.aqi, lang);
                        return (
                          <div key={i} className={`strip-item ${h.is_now ? "is-now" : ""}`}>
                            <div className="strip-time">{h.is_now ? t.now : h.time}</div>
                            <div className="strip-icon">{weatherIcon(h.weather_code, h.is_day)}</div>
                            <div className="strip-aqi" style={{ background: meta.bar }}>
                              {h.aqi}
                            </div>
                            <div className="strip-temp">{h.temp !== null ? `${h.temp}°C` : "--"}</div>
                            <div className="strip-wind">{h.wind !== null ? `${h.wind} km/h` : ""}</div>
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}

                {/* Live Ground Sensors */}
                <section className="card">
                  <div className="card-header">
                    <div className="card-title">
                      {t.sensorsTitle} ({placeData.sensors?.length || 0})
                    </div>
                  </div>
                  {placeData.sensors?.length > 0 ? (
                    <div className="sensor-list">
                      {placeData.sensors.map((s, idx) => (
                        <div key={idx} className="sensor-item">
                          <div>
                            <div className="sensor-name">{s.name}</div>
                            <div className="sensor-meta">
                              PM2.5: {s.pm25} • {s.distance_km} {t.kmAway} • {s.age_hours} {t.hrsAgo}
                            </div>
                          </div>
                          <div
                            className="sensor-aqi-pill"
                            style={{ background: getAqiMeta(s.aqi, lang).bar }}
                          >
                            {s.aqi}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="card-sub">{t.noSensors}</div>
                  )}
                </section>
              </>
            )}
          </>
        )}

        {/* TAB 2: SINDH RANKING */}
        {tab === "ranking" && (
          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">{t.rankTitle}</div>
                <div className="card-sub">{t.rankSub}</div>
              </div>
            </div>

            {loadingRank ? (
              <div className="loader-box" style={{ boxShadow: "none", border: "none", background: "transparent" }}>
                <div className="spinner" />
                <div>{t.loading}</div>
              </div>
            ) : (
              <div className="rank-list">
                {ranking.map((r, idx) => {
                  const meta = getAqiMeta(r.aqi, lang);
                  const pct = Math.min(100, Math.round((r.aqi / 250) * 100));
                  return (
                    <div key={r.city} className="rank-row" onClick={() => pickCity(r.city)}>
                      <div className="rank-num">#{idx + 1}</div>
                      <div className="rank-city">{r.city}</div>
                      <div className="rank-bar-wrap">
                        <div className="rank-bar" style={{ width: `${pct}%`, background: meta.bar }} />
                      </div>
                      <div className="rank-temp">{r.temp !== null ? `${r.temp}°C` : "--"}</div>
                      <div className="rank-aqi" style={{ background: meta.bar }}>{r.aqi}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {/* TAB 3: TRENDS */}
        {tab === "trends" && (
          <section className="card">
            <div className="card-header">
              <div className="card-title">{t.trendsTitle}</div>
            </div>

            <div className="trends-controls">
              <label htmlFor="trend-city-select">{t.selectCity}</label>
              <select
                id="trend-city-select"
                className="city-select"
                value={trendCity}
                onChange={(e) => setTrendCity(e.target.value)}
              >
                {QUICK_CITIES.map((c) => (
                  <option key={c.key} value={c.key}>
                    {c[lang]} ({c.key})
                  </option>
                ))}
              </select>
            </div>

            {loadingTrend && (
              <div className="loader-box" style={{ boxShadow: "none", border: "none", background: "transparent" }}>
                <div className="spinner" />
                <div>{t.loading}</div>
              </div>
            )}

            {!loadingTrend && trendData?.ok && (
              <>
                <div className="stat-row">
                  {trendData.cleanest && (
                    <div className="stat-card">
                      <div className="tom-meta">{t.cleanest24}</div>
                      <div
                        className="tom-aqi"
                        style={{ color: getAqiMeta(trendData.cleanest.aqi, lang).bar }}
                      >
                        AQI {trendData.cleanest.aqi}
                      </div>
                      <div className="tom-meta">{trendData.cleanest.time}</div>
                    </div>
                  )}
                  {trendData.peak && (
                    <div className="stat-card">
                      <div className="tom-meta">{t.peak24}</div>
                      <div
                        className="tom-aqi"
                        style={{ color: getAqiMeta(trendData.peak.aqi, lang).bar }}
                      >
                        AQI {trendData.peak.aqi}
                      </div>
                      <div className="tom-meta">{trendData.peak.time}</div>
                    </div>
                  )}
                </div>

                <div className="card" style={{ boxShadow: "none" }}>
                  <div className="card-title" style={{ marginBottom: 10 }}>{t.chart72}</div>
                  <SimpleLineChart
                    data={trendData.hourly_72h}
                    valueKey="aqi"
                    labelKey="time"
                    stroke="#14b8a6"
                  />
                </div>

                <div className="card" style={{ boxShadow: "none", marginBottom: 0 }}>
                  <div className="card-title" style={{ marginBottom: 10 }}>{t.chart30}</div>
                  <SimpleLineChart
                    data={trendData.daily_30d}
                    valueKey="aqi"
                    labelKey="date"
                    stroke="#38bdf8"
                  />
                </div>
              </>
            )}
          </section>
        )}

        {/* TAB 4: ABOUT */}
        {tab === "about" && (
          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">{t.aboutTitle}</div>
                <div className="card-sub">{t.aboutSub}</div>
              </div>
            </div>

            <div className="about-grid">
              <div className="about-box">
                <h3>{t.aboutMissionTitle}</h3>
                <p>{t.aboutMissionText}</p>
              </div>
              <div className="about-box">
                <h3>{t.aboutDataTitle}</h3>
                <ul>
                  {t.aboutDataPoints.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              </div>
              <div className="about-box">
                <h3>{t.aboutAccessTitle}</h3>
                <ul>
                  {t.aboutAccessPoints.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="card-title" style={{ marginBottom: 10 }}>{t.scaleTitle}</div>
            <div className="scale-list">
              {AQI_SCALE.map((row) => (
                <div key={row.key} className="scale-row">
                  <span className="scale-badge" style={{ background: row.color }}>
                    {row.range}
                  </span>
                  <span className="scale-name">{t.cats[row.key].label}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        <footer className="footer">{t.footer}</footer>
      </div>
    </>
  );
}