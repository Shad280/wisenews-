import os
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# Optional: Twitter
import tweepy

# Optional: YouTube/Whisper
import subprocess
import whisper

# --- CONFIG ---
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Performance Configuration
MAX_ARTICLES_PER_SOURCE = 3  # Reduced from 5 to handle more sources efficiently
ENABLE_RATE_LIMITING = True  # Add delays between requests to avoid overwhelming servers
REQUEST_DELAY = 0.5  # Seconds to wait between requests

# Regional Configuration - Enable/disable different regions
ENABLE_US_SOURCES = True
ENABLE_EUROPEAN_SOURCES = True  
ENABLE_ASIAN_SOURCES = True
ENABLE_MIDDLE_EAST_SOURCES = True
ENABLE_AFRICAN_SOURCES = True
ENABLE_LATIN_AMERICAN_SOURCES = True
ENABLE_CANADIAN_SOURCES = True

# Topic Configuration - Enable/disable different categories
ENABLE_MAINSTREAM_NEWS = True
ENABLE_BUSINESS_TECH = True
ENABLE_SCIENCE_HEALTH = True
ENABLE_ALTERNATIVE_MEDIA = True
ENABLE_WIRE_SERVICES = True
ENABLE_SPECIALIZED_TOPICS = True

# RSS feeds for major news
RSS_URLS = [
    # Major International News
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.skynews.com/feeds/rss/home.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.theguardian.com/world/rss",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    
    # US News Sources
    "https://feeds.washingtonpost.com/rss/world",
    "https://www.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.abcnews.go.com/abcnews/topstories",
    "https://feeds.nbcnews.com/nbcnews/public/world",
    "https://feeds.foxnews.com/foxnews/latest",
    "https://feeds.usatoday.com/news/topstories",
    "https://feeds.cbsnews.com/CBSNewsMain",
    "https://feeds.cbsnews.com/CBSNewsWorld",
    "https://feeds.pbs.org/newshour/rss/nation",
    "https://feeds.feedburner.com/msnbc/main",
    "https://feeds.feedburner.com/cnn-topstories",
    "https://feeds.feedburner.com/cnn-world",
    "https://feeds.feedburner.com/politico",
    "https://feeds.feedburner.com/TheHill",
    "https://feeds.feedburner.com/HuffingtonPost",
    "https://feeds.latimes.com/latimes/news",
    "https://feeds.feedburner.com/usnews-world",
    
    # European News
    "https://feeds.dw.com/dw/en/news",  # Deutsche Welle
    "https://feeds.euronews.com/en/news",
    "https://www.france24.com/en/rss",
    "https://feeds.feedburner.com/euronews/en/home",
    "https://www.thelocal.com/feeds/rss/news",
    "https://feeds.feedburner.com/spiegel-international",
    "https://feeds.feedburner.com/rt-news",
    "https://feeds.feedburner.com/rfi-english",
    "https://feeds.ansa.it/ansa/english",
    "https://feeds.swissinfo.ch/eng/swissinfo.ch-news",
    "https://feeds.feedburner.com/TheIrishTimes-BreakingNews",
    "https://feeds.feedburner.com/independent-news",
    "https://feeds.feedburner.com/telegraph-news",
    "https://feeds.feedburner.com/express-news",
    "https://feeds.feedburner.com/mirror-news",
    
    # Business & Tech
    "https://feeds.bloomberg.com/politics/news.rss",
    "https://feeds.bloomberg.com/technology/news.rss",
    "https://feeds.fortune.com/fortune/headlines",
    "https://feeds.wsj.com/wsj/xml/rss/3_7041.xml",  # Wall Street Journal
    "https://feeds.feedburner.com/techcrunch/startups",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://feeds.feedburner.com/businessinsider",
    "https://feeds.feedburner.com/forbes/business",
    "https://feeds.feedburner.com/reuters/business",
    "https://feeds.feedburner.com/venturebeat",
    "https://feeds.feedburner.com/TheNextWeb",
    "https://feeds.feedburner.com/engadget",
    "https://feeds.feedburner.com/wired",
    "https://feeds.feedburner.com/fastcompany",
    "https://feeds.feedburner.com/MarketWatch-TopStories",
    "https://feeds.feedburner.com/cnbc-technology",
    "https://feeds.feedburner.com/cnet-news",
    "https://feeds.feedburner.com/zdnet-breaking-news",
    
    # Major Financial News Sources
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/economics/news.rss",
    "https://feeds.bloomberg.com/businessweek/news.rss",
    "https://www.wsj.com/xml/rss/3_7014.xml",  # WSJ Markets
    "https://www.wsj.com/xml/rss/3_7031.xml",  # WSJ Economy
    "https://www.wsj.com/xml/rss/3_7204.xml",  # WSJ Personal Finance
    "https://www.ft.com/rss/home/us",          # Financial Times US
    "https://www.ft.com/rss/home/uk",          # Financial Times UK
    "https://www.ft.com/rss/companies",        # Financial Times Companies
    "https://feeds.reuters.com/news/wealth",   # Reuters Wealth
    "https://feeds.reuters.com/reuters/UKPersonalFinance",
    "https://feeds.reuters.com/reuters/USPersonalFinance",
    
    # Market & Trading News
    "https://feeds.marketwatch.com/marketwatch/marketpulse/",
    "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
    "https://feeds.marketwatch.com/marketwatch/StockstoWatch/",
    "https://feeds.cnbc.com/cn/CNBC_US_News",
    "https://feeds.cnbc.com/cn/CNBC_World_News",
    "https://feeds.cnbc.com/cn/CNBC_US_Top_News_and_Analysis",
    "https://feeds.benzinga.com/benzinga",
    "https://feeds.feedburner.com/zerohedge/feed",
    "https://feeds.feedburner.com/SeekingAlphaAll",
    "https://feeds.feedburner.com/InvestorPlace",
    "https://feeds.feedburner.com/TheMotleyFool",
    "https://feeds.feedburner.com/Kiplinger",
    "https://feeds.feedburner.com/SmartMoney",
    "https://feeds.feedburner.com/MoneyMagazine",
    "https://feeds.feedburner.com/barrons-headlines",
    
    # Cryptocurrency & Fintech
    "https://feeds.feedburner.com/CoinDesk",
    "https://feeds.feedburner.com/CoinTelegraph",
    "https://feeds.feedburner.com/CryptoSlate",
    "https://feeds.feedburner.com/BitcoinMagazine",
    "https://feeds.feedburner.com/TheBlock",
    "https://feeds.feedburner.com/Decrypt-co",
    "https://feeds.feedburner.com/FinTechNews",
    "https://feeds.feedburner.com/PaymentsSource",
    "https://feeds.feedburner.com/AmericanBanker",
    "https://feeds.feedburner.com/DigitalTransactions",
    
    # Investment & Trading Platforms
    "https://feeds.feedburner.com/ETFcom",
    "https://feeds.feedburner.com/ETFTrends",
    "https://feeds.feedburner.com/MutualFundWire",
    "https://feeds.feedbarron.com/HedgeFundNews",
    "https://feeds.feedburner.com/InstitutionalInvestor",
    "https://feeds.feedburner.com/PensionsInvestments",
    "https://feeds.feedburner.com/AlternativeInvestmentNews",
    "https://feeds.feedburner.com/PrivateEquityWire",
    "https://feeds.feedburner.com/VentureCapitalJournal",
    
    # International Financial Markets
    "https://feeds.feedburner.com/nikkei-asia-markets",
    "https://feeds.feedburner.com/euromoneycom",
    "https://feeds.feedburner.com/GlobalCapital",
    "https://feeds.feedburner.com/IFRMarkets",
    "https://feeds.feedburner.com/AsianInvestor",
    "https://feeds.feedburner.com/FinanceAsia",
    "https://feeds.feedburner.com/ChinaBusinessNews",
    "https://feeds.feedburner.com/EconomicTimes-Markets",
    "https://feeds.feedburner.com/MoneyControlMarkets",
    "https://feeds.feedburner.com/LiveMintMarkets",
    
    # Economic Research & Analysis
    "https://feeds.feedburner.com/MoodysAnalytics",
    "https://feeds.feedburner.com/StandardPoors",
    "https://feeds.feedburner.com/FitchRatings",
    "https://feeds.feedburner.com/McKinseyInsights",
    "https://feeds.feedburner.com/BCGInsights",
    "https://feeds.feedburner.com/DeloitteInsights",
    "https://feeds.feedburner.com/PwCInsights",
    "https://feeds.feedburner.com/KPMGInsights",
    "https://feeds.feedburner.com/EconomistIntelligence",
    "https://feeds.feedburner.com/BrookingsEconomy",
    
    # Central Banks & Government Financial News
    "https://feeds.federalreserve.gov/news/all.xml",
    "https://feeds.feedburner.com/ECBNews",
    "https://feeds.feedburner.com/BankOfEnglandNews",
    "https://feeds.feedburner.com/BankOfJapanNews",
    "https://feeds.feedburner.com/PBOCNews",
    "https://feeds.feedburner.com/TreasuryGovNews",
    "https://feeds.feedburner.com/SECNews",
    "https://feeds.feedburner.com/CFTCNews",
    "https://feeds.feedburner.com/FDICNews",
    
    # Commodities & Energy Markets
    "https://feeds.feedburner.com/OilPrice",
    "https://feeds.feedburner.com/PlattsNews",
    "https://feeds.feedburner.com/EnergyNewsToday",
    "https://feeds.feedburner.com/GoldPrice",
    "https://feeds.feedburner.com/KitcoNews",
    "https://feeds.feedburner.com/MetalMiner",
    "https://feeds.feedburner.com/CommodityHQ",
    "https://feeds.feedburner.com/AgricultureNews",
    "https://feeds.feedburner.com/FarmFutures",
    
    # Personal Finance & Wealth Management
    "https://feeds.feedburner.com/NerdWallet",
    "https://feeds.feedburner.com/Bankrate",
    "https://feeds.feedburner.com/CreditCards",
    "https://feeds.feedburner.com/LendingTree",
    "https://feeds.feedburner.com/WealthManagement",
    "https://feeds.feedburner.com/ThinkAdvisor",
    "https://feeds.feedburner.com/InvestmentNews",
    "https://feeds.feedburner.com/FinancialPlanning",
    "https://feeds.feedburner.com/RetirementPlanAdvisor",
    
    # Science & Health
    "https://rss.sciam.com/ScientificAmerican-Global",
    "https://feeds.nature.com/nature/rss/current",
    "https://feeds.feedburner.com/reuters/scienceNews",
    "https://feeds.feedburner.com/reuters/health",
    "https://feeds.feedburner.com/sciencedaily",
    "https://feeds.feedburner.com/newscientist",
    "https://feeds.feedburner.com/livescience",
    "https://feeds.feedburner.com/phys-org",
    "https://feeds.feedburner.com/medicalnews",
    "https://feeds.feedburner.com/healthday",
    "https://feeds.feedburner.com/webmd-news",
    "https://feeds.feedburner.com/cdc-health-news",
    
    # Additional High-Quality International
    "https://feeds.feedburner.com/ap-world-news",     # Associated Press
    "https://feeds.feedburner.com/time/world",        # Time Magazine
    "https://feeds.feedburner.com/time/topstories",
    "https://feeds.feedburner.com/newsweek",
    "https://feeds.feedburner.com/associated-press",
    "https://feeds.propublica.org/propublica/main",   # Investigative journalism
    "https://feeds.feedburner.com/christiansciencemonitor/world", # CS Monitor
    "https://feeds.feedburner.com/upi-topnews",
    "https://feeds.feedburner.com/thedailybeast",
    "https://feeds.feedburner.com/theatlantic",
    "https://feeds.feedburner.com/newrepublic",
    "https://feeds.feedburner.com/motherjones",
    "https://feeds.feedburner.com/reason",
    "https://feeds.feedburner.com/townhall",
    
    # Asia-Pacific
    "https://www.scmp.com/rss/91/feed",              # South China Morning Post
    "https://feeds.feedburner.com/japantimes",       # Japan Times
    "https://feeds.theage.com.au/rssfeeds/world/rss.xml",        # The Age (Australia)
    "https://feeds.reuters.com/Reuters/worldNews",   # Reuters World
    "https://feeds.feedburner.com/nikkei-english",   # Nikkei
    "https://feeds.feedburner.com/asahi-english",    # Asahi Shimbun
    "https://feeds.feedburner.com/straitstimes",     # Straits Times
    "https://feeds.feedburner.com/thehindu",         # The Hindu
    "https://feeds.feedburner.com/timesofindianews", # Times of India
    "https://feeds.feedburner.com/ndtv-news",        # NDTV
    "https://feeds.feedburner.com/sydney-morning-herald",
    "https://feeds.feedburner.com/australian-news",
    "https://feeds.feedburner.com/nzherald",         # New Zealand Herald
    "https://feeds.feedburner.com/bangkokpost",      # Bangkok Post
    "https://feeds.feedburner.com/jakarta-post",     # Jakarta Post
    "https://feeds.feedburner.com/koreatimes",       # Korea Times
    "https://feeds.feedburner.com/channelnewsasia",  # Channel NewsAsia
    
    # Middle East/Africa
    "https://feeds.feedburner.com/middle-east-eye",  # Middle East Eye
    "https://feeds.feedburner.com/haaretz",          # Haaretz (Israel)
    "https://feeds.feedburner.com/jpost",            # Jerusalem Post
    "https://feeds.feedburner.com/ynetnews",         # Ynet News
    "https://feeds.feedburner.com/timesofisrael",    # Times of Israel
    "https://feeds.feedburner.com/dailynewsegypt",   # Daily News Egypt
    "https://feeds.feedburner.com/gulfnews",         # Gulf News
    "https://feeds.feedburner.com/khaleejtimes",     # Khaleej Times
    "https://feeds.feedburner.com/arabnews",         # Arab News
    "https://feeds.feedburner.com/dailystar-lebanon", # Daily Star Lebanon
    "https://feeds.feedburner.com/moroccoworld",     # Morocco World News
    "https://feeds.feedburner.com/allafrica",        # AllAfrica
    "https://feeds.feedburner.com/iol-news",         # IOL (South Africa)
    "https://feeds.feedburner.com/news24",           # News24 (South Africa)
    "https://feeds.feedburner.com/mg-africa",        # Mail & Guardian Africa
    
    # Latin America
    "https://feeds.feedburner.com/eluniversal-english", # El Universal
    "https://feeds.feedburner.com/clarin-english",   # Clarín
    "https://feeds.feedburner.com/folha-english",    # Folha de S.Paulo
    "https://feeds.feedburner.com/elnuevoherald",    # El Nuevo Herald
    "https://feeds.feedburner.com/milenio-english",  # Milenio
    "https://feeds.feedburner.com/eltiempo-english", # El Tiempo
    "https://feeds.feedburner.com/globo-english",    # O Globo
    "https://feeds.feedburner.com/buenosairesherald", # Buenos Aires Herald
    "https://feeds.feedburner.com/rionegro-english", # Río Negro
    
    # Canada
    "https://feeds.feedburner.com/cbc-topstories",   # CBC
    "https://feeds.feedburner.com/globeandmail",     # Globe and Mail
    "https://feeds.feedburner.com/nationalpost",     # National Post
    "https://feeds.feedburner.com/macleans",         # Maclean's
    "https://feeds.feedburner.com/torontostar",      # Toronto Star
    "https://feeds.feedburner.com/montrealgazette",  # Montreal Gazette
    "https://feeds.feedburner.com/vancouversun",     # Vancouver Sun
    
    # Independent/Alternative Media
    "https://feeds.democracynow.org/democracynow",    # Democracy Now
    "https://feeds.commondreams.org/commondreams",    # Common Dreams
    "https://feeds.feedburner.com/tyt-main",         # The Young Turks
    "https://feeds.feedburner.com/intercept",        # The Intercept
    "https://feeds.feedburner.com/alternet",         # AlterNet
    "https://feeds.feedburner.com/truthout",         # Truthout
    "https://feeds.feedburner.com/counterpunch",     # CounterPunch
    "https://feeds.feedburner.com/zmag",             # Z Magazine
    "https://feeds.feedburner.com/indymedia",        # Indymedia
    "https://feeds.feedburner.com/wikileaks",        # WikiLeaks
    "https://feeds.feedburner.com/publicintegrity",  # Center for Public Integrity
    "https://feeds.feedburner.com/opensecrets",      # OpenSecrets
    
    # Specialized Topics
    "https://feeds.feedburner.com/defense-news",     # Defense News
    "https://feeds.feedburner.com/military-news",    # Military.com
    "https://feeds.feedburner.com/space-news",       # SpaceNews
    "https://feeds.feedburner.com/nasa-news",        # NASA News
    "https://feeds.feedburner.com/energy-news",      # Energy News
    "https://feeds.feedburner.com/climate-news",     # Climate News
    "https://feeds.feedburner.com/environmental-news", # Environmental News
    "https://feeds.feedburner.com/education-news",   # Education News
    "https://feeds.feedburner.com/sports-news",      # Sports News
    "https://feeds.feedburner.com/entertainment-news", # Entertainment News
    
    # Wire Services & Agencies
    "https://feeds.feedburner.com/ap-breaking-news",
    "https://feeds.feedburner.com/reuters-breaking-news",
    "https://feeds.feedburner.com/bloomberg-breaking-news",
    "https://feeds.feedburner.com/afp-english",      # Agence France-Presse
    "https://feeds.feedburner.com/dpa-english",      # Deutsche Presse-Agentur
    "https://feeds.feedburner.com/efe-english",      # EFE Agency
    "https://feeds.feedburner.com/ansa-english",     # ANSA
    "https://feeds.feedburner.com/xinhua-english",   # Xinhua News Agency
    "https://feeds.feedburner.com/tass-english",     # TASS
    "https://feeds.feedburner.com/itar-tass-english", # ITAR-TASS
]

# Twitter (X) API setup - Comprehensive global news sources
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAFOc3QEAAAAAwFWgGM%2FJnepYkyVyrsn5WZzcMRI%3DQtDxII81yUK8iqMygdKw72WP8N3q36piLtJPSpCic1qEig4Jea"
TWITTER_USER_IDS = {
    # Major US Networks
    "CNN": "759251",
    "BBCWorld": "742143", 
    "SkyNews": "7587032",
    "FoxNews": "1367531",
    "NBCNews": "14173315",
    "ABCNews": "28785486",
    "CBSNews": "15012486",
    "NPR": "5392522",
    
    # International News
    "Reuters": "1652541",
    "AP": "51241574",
    "BBCBreaking": "5402612",
    "AlJazeera": "7683912",
    "France24": "15460853",
    "DeutscheWelle": "3108479576",
    "EuroNews": "41550356",
    
    # Newspapers & Magazines
    "nytimes": "807095",
    "WSJ": "3108351",
    "washingtonpost": "2467791",
    "guardian": "87818409",
    "TheEconomist": "5988062",
    "TIME": "14293310",
    "USATODAY": "15754281",
    "HuffPost": "14511951",
    "POLITICO": "9300262",
    
    # Business & Tech
    "Bloomberg": "34713362",
    "Forbes": "91478624",
    "TechCrunch": "816653",
    "WIRED": "1344951",
    "engadget": "14372486",
    "verge": "275686563",
    "arstechnica": "717313",
    
    # Financial Markets & Trading
    "MarketWatch": "24743517",
    "CNBCnow": "20402945",
    "FinancialTimes": "18949452",
    "Benzinga": "2911051", 
    "SeekingAlpha": "25076334",
    "zerohedge": "18733659",
    "TheMotleyFool": "32998242",
    "Barrons": "17285008",
    "InvestorPlace": "115750815",
    
    # Cryptocurrency & Fintech
    "CoinDesk": "87667621",
    "cointelegraph": "2207129125",
    "coinbase": "4103513080",
    "binance": "877807935493033984",
    "krakenfx": "819033742116655104",
    "ethereum": "731035064",
    "bitcoin": "357312062",
    "CryptoSlate": "907536539",
    "TheBlock__": "829814961883422721",
    "Decrypt_co": "826510509689638913",
    
    # Investment Firms & Analysis
    "BlackRock": "239473516",
    "Vanguard_Group": "8735932",
    "MorganStanley": "80210467",
    "GoldmanSachs": "15007989",
    "jpmorgan": "22060179",
    "BankofAmerica": "2996136119",
    "CitiBusiness": "14473055",
    "McKinsey": "113976206",
    "BCG": "68144808",
    "DeloitteUS": "13749842",
    
    # Economic Analysts & Research
    "neilirwin": "479017132",
    "nickgrundy": "15110137",
    "jimcramer": "103754003",
    "elonmusk": "44196397",
    "cathiedwood": "1291545780",
    "chamath": "3291691",
    "RayDalio": "39664347",
    "GaryVee": "17737278",
    "Naval": "745273",
    
    # Central Banks & Government
    "federalreserve": "34385690",
    "ecb": "16304555",
    "bankofengland": "1260544726",
    "USTreasury": "62985782",
    "SEC_News": "32471755",
    "CFTCgov": "79302892",
    
    # Science & Health
    "NatureNews": "18835209",
    "ScienceMagazine": "182613062",
    "SciAm": "14647570",
    "WHO": "14499829",
    "CDCgov": "146569971",
    
    # Regional Sources
    "SCMPNews": "17943800",      # South China Morning Post
    "STcom": "5081761",         # Straits Times
    "thehindu": "20751449",     # The Hindu
    "ToIIndiaNews": "2446647",  # Times of India
    "JerusalemPost": "26166749", # Jerusalem Post
    "ArabNews": "373839802",    # Arab News
    
    # Wire Services
    "AFPnews": "380648579",     # Agence France-Presse
    "XinhuaNews": "2606335486", # Xinhua News
    "RTnews": "24743137",       # RT News
    
    # Alternative/Independent
    "democracynow": "1591493",
    "WikiLeaks": "16589312",
    "TheIntercept": "2479634806",
    "ProPublica": "13437142",
}
TWEETS_PER_SOURCE = 3  # Reduced to avoid rate limits with more sources

# YouTube links - Comprehensive news channels for transcription
YOUTUBE_LINKS = [
    # Example news videos (replace with actual URLs from channels below)
    # "https://www.youtube.com/watch?v=VIDEO_ID",
    # "https://www.youtube.com/watch?v=ANOTHER_VIDEO_ID",
    
    # Major International News Channels:
    # BBC News: https://www.youtube.com/@BBCNews
    # CNN: https://www.youtube.com/@CNN  
    # Sky News: https://www.youtube.com/@SkyNews
    # Reuters: https://www.youtube.com/@Reuters
    # Associated Press: https://www.youtube.com/@AP
    # Al Jazeera English: https://www.youtube.com/@aljazeeraenglish
    # France 24: https://www.youtube.com/@FRANCE24English
    # DW News: https://www.youtube.com/@DWNews
    # Euronews: https://www.youtube.com/@euronews
    # Russia Today: https://www.youtube.com/@RT
    
    # US News Networks:
    # Fox News: https://www.youtube.com/@FoxNews
    # ABC News: https://www.youtube.com/@ABCNews
    # NBC News: https://www.youtube.com/@NBCNews
    # CBS News: https://www.youtube.com/@CBSNews
    # PBS NewsHour: https://www.youtube.com/@PBSNewsHour
    # MSNBC: https://www.youtube.com/@msnbc
    # CNBC: https://www.youtube.com/@CNBC
    # NPR: https://www.youtube.com/@NPR
    
    # Business & Finance:
    # Bloomberg: https://www.youtube.com/@BloombergTelevision
    # Financial Times: https://www.youtube.com/@FinancialTimes
    # Wall Street Journal: https://www.youtube.com/@WSJ
    # CNBC: https://www.youtube.com/@CNBC
    # CNBC International: https://www.youtube.com/@CNBCInternational
    # MarketWatch: https://www.youtube.com/@MarketWatch
    # Yahoo Finance: https://www.youtube.com/@YahooFinance
    # Benzinga: https://www.youtube.com/@Benzinga
    # TheStreet: https://www.youtube.com/@TheStreet
    # Mad Money w/ Jim Cramer: https://www.youtube.com/@MadMoneyOnCNBC
    # Fast Money: https://www.youtube.com/@CNBCFastMoney
    # Squawk Box: https://www.youtube.com/@SquawkCNBC
    # Closing Bell: https://www.youtube.com/@ClosingBell
    
    # Cryptocurrency & Fintech:
    # CoinDesk: https://www.youtube.com/@CoinDesk
    # Coin Bureau: https://www.youtube.com/@CoinBureau
    # InvestAnswers: https://www.youtube.com/@InvestAnswers
    # Altcoin Daily: https://www.youtube.com/@AltcoinDaily
    # Coin Telegraph: https://www.youtube.com/@Cointelegraph
    # Binance: https://www.youtube.com/@BinanceOfficial
    # Coinbase: https://www.youtube.com/@Coinbase
    # Crypto Zombie: https://www.youtube.com/@CryptoZombie
    # DataDash: https://www.youtube.com/@DataDash
    # The Modern Investor: https://www.youtube.com/@TheModernInvestor
    
    # Investment Education & Analysis:
    # Ben Felix: https://www.youtube.com/@BenFelixCSI
    # Two Cents: https://www.youtube.com/@TwoCentsPBS
    # The Plain Bagel: https://www.youtube.com/@ThePlainBagel
    # Patrick Boyle: https://www.youtube.com/@PBoyle
    # Aswath Damodaran: https://www.youtube.com/@AswathDamodaranOnValuation
    # Ray Dalio: https://www.youtube.com/@RayDalio
    # Khan Academy Finance: https://www.youtube.com/@KhanAcademyFinance
    # Zacks Investment Research: https://www.youtube.com/@ZacksInvestmentResearch
    # Morningstar: https://www.youtube.com/@MorningstarInc
    # Seeking Alpha: https://www.youtube.com/@SeekingAlpha
    
    # Personal Finance:
    # Dave Ramsey: https://www.youtube.com/@DaveRamseyShow
    # Graham Stephan: https://www.youtube.com/@GrahamStephan
    # Andrei Jikh: https://www.youtube.com/@AndreiJikh
    # Meet Kevin: https://www.youtube.com/@MeetKevin
    # Minority Mindset: https://www.youtube.com/@MinorityMindset
    # The Financial Diet: https://www.youtube.com/@thefinancialdiet
    # Nate O'Brien: https://www.youtube.com/@NateOBrien
    # Ryan Kaji: https://www.youtube.com/@RyansWorld
    # The Motley Fool Money: https://www.youtube.com/@TheMotleyFool
    
    # Economic Analysis & Policy:
    # Federal Reserve: https://www.youtube.com/@federalreserve
    # Council on Foreign Relations: https://www.youtube.com/@cfr
    # Brookings Institution: https://www.youtube.com/@BrookingsInst
    # American Enterprise Institute: https://www.youtube.com/@AEIVideos
    # Peterson Institute: https://www.youtube.com/@PIIE
    # World Economic Forum: https://www.youtube.com/@WorldEconomicForum
    # International Monetary Fund: https://www.youtube.com/@IMFNews
    # World Bank: https://www.youtube.com/@WorldBank
    
    # Regional Channels:
    # NHK World: https://www.youtube.com/@NHKWorldTV
    # CGTN: https://www.youtube.com/@cgtn
    # CCTV News: https://www.youtube.com/@CCTVNews
    # TRT World: https://www.youtube.com/@TRTWorld
    # WION: https://www.youtube.com/@WION
    # CNA: https://www.youtube.com/@ChannelNewsAsia
    # CBC News: https://www.youtube.com/@CBCNews
    # Global News: https://www.youtube.com/@GlobalNews
    
    # Independent/Alternative:
    # Democracy Now: https://www.youtube.com/@democracynow
    # The Young Turks: https://www.youtube.com/@TheYoungTurks
    # Breaking Points: https://www.youtube.com/@breakingpoints
    # The Hill: https://www.youtube.com/@thehill
    # Secular Talk: https://www.youtube.com/@SecularTalk
    # The Majority Report: https://www.youtube.com/@majorityfm
    
    # Specialized Topics:
    # NASA: https://www.youtube.com/@NASA
    # SpaceX: https://www.youtube.com/@SpaceX
    # World Health Organization: https://www.youtube.com/@WHO
    # United Nations: https://www.youtube.com/@UN
    # Pentagon Channel: https://www.youtube.com/@thepentagon
    # White House: https://www.youtube.com/@whitehouse
    
    # To use: Copy a specific video URL from any of these channels
    # Example: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
]

# --- HELPERS ---
def fetch_article_text(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        res.raise_for_status()  # Raises an HTTPError for bad responses
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extract text from paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            return '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
        else:
            # Fallback: try to get any text content
            return soup.get_text()[:1000] + "..."
            
    except requests.exceptions.Timeout:
        return "Error: Request timed out after 10 seconds"
    except requests.exceptions.RequestException as e:
        return f"Error fetching article: {e}"
    except Exception as e:
        return f"Error parsing article: {e}"

def save_to_file(content, title, prefix=""):
    """Save content to file with duplicate checking"""
    import hashlib
    import sqlite3
    
    # Generate a content hash to check for duplicates
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
    filename = f"{prefix}{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    
    # Check if similar content already exists in database
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check for existing content with same hash
        cursor.execute('SELECT filename FROM articles WHERE content_hash = ?', (content_hash,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"🔄 Duplicate content detected, skipping: {title[:50]}... (matches: {existing[0]})")
            conn.close()
            return None
            
        # Check for similar title
        cursor.execute('SELECT filename FROM articles WHERE title LIKE ?', (f'%{safe_title[:30]}%',))
        existing_title = cursor.fetchone()
        
        if existing_title:
            print(f"🔄 Similar title detected, skipping: {title[:50]}... (matches: {existing_title[0]})")
            conn.close()
            return None
            
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not check for duplicates: {e}")
        # Continue saving if database check fails
    
    # Check if file with same content already exists
    for existing_file in os.listdir(DOWNLOADS_DIR):
        if existing_file.endswith('.txt'):
            try:
                with open(os.path.join(DOWNLOADS_DIR, existing_file), 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                    existing_hash = hashlib.md5(existing_content.encode('utf-8')).hexdigest()
                    
                if existing_hash == content_hash:
                    print(f"🔄 Duplicate file content detected, skipping: {title[:50]}... (matches: {existing_file})")
                    return None
                    
            except Exception:
                continue  # Skip if can't read file
    
    # Save the new file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Saved new article: {filepath}")
    return filepath

def fetch_rss_articles(rss_url, limit=None):
    if limit is None:
        limit = MAX_ARTICLES_PER_SOURCE
        
    try:
        print(f"🔄 Fetching from: {rss_url}")
        feed = feedparser.parse(rss_url)
        articles = []
        
        if not feed.entries:
            print(f"❌ No articles found in RSS feed: {rss_url}")
            return articles
            
        for entry in feed.entries[:limit]:
            try:
                if ENABLE_RATE_LIMITING:
                    import time
                    time.sleep(REQUEST_DELAY)
                    
                content = fetch_article_text(entry.link)
                articles.append({"title": entry.title, "content": content})
                print(f"✅ Fetched: {entry.title[:60]}...")
            except Exception as e:
                print(f"❌ Failed to fetch article '{entry.title[:60]}...': {e}")
                continue
                
        print(f"✅ Successfully fetched {len(articles)} articles from {rss_url}")
        return articles
        
    except Exception as e:
        print(f"❌ Failed to fetch RSS feed {rss_url}: {e}")
        return []

def fetch_tweets():
    try:
        print("🔄 Connecting to Twitter API...")
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        
        for name, user_id in TWITTER_USER_IDS.items():
            try:
                print(f"🔄 Fetching tweets from {name}...")
                tweets = client.get_users_tweets(id=user_id, max_results=TWEETS_PER_SOURCE)
                
                if tweets.data:
                    for tweet in tweets.data:
                        save_to_file(tweet.text, f"{name}_tweet_{tweet.id}", prefix="TW_")
                    print(f"✅ Successfully fetched {len(tweets.data)} tweets from {name}")
                else:
                    print(f"⚠️ No tweets found for {name}")
                    
            except tweepy.TooManyRequests as e:
                print(f"❌ Rate limit hit for {name}: {e}")
                print("⏳ Waiting might be needed before next Twitter request")
                continue
            except tweepy.Unauthorized as e:
                print(f"❌ Unauthorized access for {name}: {e}")
                continue
            except Exception as e:
                print(f"❌ Failed to fetch tweets from {name}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Twitter API connection failed: {e}")
        print("Continuing with other news sources...")

def download_youtube_audio(youtube_url):
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3",
        "-o", f"{DOWNLOADS_DIR}/%(title)s.%(ext)s", youtube_url
    ]
    subprocess.run(cmd, check=True)
    for file in os.listdir(DOWNLOADS_DIR):
        if file.endswith(".mp3"):
            return os.path.join(DOWNLOADS_DIR, file)
    return None

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['text']

# --- MAIN PIPELINE ---
def run_pipeline():
    print("🚀 Starting news aggregation pipeline...")
    print(f"📊 Configured to process {len(RSS_URLS)} RSS sources")
    total_articles = 0
    
    # 1. RSS/Text Articles
    print("\n📰 Processing RSS feeds...")
    for i, rss in enumerate(RSS_URLS, 1):
        try:
            print(f"\n📍 Processing source {i}/{len(RSS_URLS)}")
            articles = fetch_rss_articles(rss)
            for article in articles:
                save_to_file(article['content'], article['title'], prefix="RSS_")
                total_articles += 1
        except Exception as e:
            print(f"❌ Error processing RSS feed {rss}: {e}")
            print("Continuing with next RSS feed...")
            continue

    # 2. Twitter
    print(f"\n🐦 Processing Twitter feeds...")
    if TWITTER_BEARER_TOKEN and TWITTER_USER_IDS:
        try:
            fetch_tweets()
        except Exception as e:
            print(f"❌ Twitter processing failed: {e}")
            print("Continuing with other sources...")
    else:
        print("⚠️ Twitter disabled - no Bearer Token or User IDs")

    # 3. YouTube Videos
    print(f"\n🎥 Processing YouTube videos...")
    if YOUTUBE_LINKS:
        for yt_url in YOUTUBE_LINKS:
            try:
                print(f"🔄 Processing YouTube: {yt_url}")
                audio_path = download_youtube_audio(yt_url)
                if audio_path:
                    transcript = transcribe_audio(audio_path)
                    save_to_file(transcript, os.path.basename(audio_path), prefix="YT_")
                    os.remove(audio_path)
                    total_articles += 1
            except Exception as e:
                print(f"❌ Failed to process YouTube video {yt_url}: {e}")
                print("Continuing with next video...")
                continue
    else:
        print("⚠️ No YouTube links configured")

    print(f"\n✅ Pipeline completed! Total content saved: {total_articles} files")
    print("📁 Check the 'downloads' folder for all saved content.")
    print(f"🌍 Processed {len(RSS_URLS)} RSS sources from around the world")

if __name__ == "__main__":
    run_pipeline()