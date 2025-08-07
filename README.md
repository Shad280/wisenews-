# WiseNews - Intelligent News Aggregation Platform

![WiseNews](https://img.shields.io/badge/WiseNews-v1.0-blue) ![Flask](https://img.shields.io/badge/Flask-2.3.3-green) ![Python](https://img.shields.io/badge/Python-3.11+-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

A modern, intelligent news aggregation platform built with Flask, featuring a beautiful responsive design, powerful search capabilities, and a comprehensive REST API.

## 🌟 Features

### Core Functionality
- **Intelligent News Aggregation**: Advanced article management and categorization system
- **Real-time Search**: Fast, powerful search across all articles with highlighting
- **Category Organization**: Articles organized into Technology, Features, Guide, and Updates
- **Responsive Design**: Beautiful, mobile-first UI built with Bootstrap 5
- **RESTful API**: Complete API endpoints for integration with other applications

### User Experience
- **Modern Interface**: Clean, professional design with smooth animations
- **Mobile Optimized**: Perfect experience across all devices
- **Fast Performance**: Optimized for speed and reliability
- **Social Sharing**: Built-in sharing capabilities for articles
- **Search Suggestions**: Intelligent search suggestions and filters

### Technical Features
- **SQLite Database**: Lightweight, efficient data storage
- **API Documentation**: Comprehensive API with health checks
- **Error Handling**: Robust error handling and logging
- **Security**: Built-in security features and best practices
- **Scalable Architecture**: Designed for easy scaling and deployment

## 🚀 Live Demo

**Production URL**: [https://wisenews-app.onrender.com](https://wisenews-app.onrender.com)

The application is deployed on Render.com with automatic deployments from the main branch.

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Features](#features-detailed)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wisenews.git
   cd wisenews
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## ⚡ Quick Start

### Running Locally
```bash
# Install dependencies
pip install flask gunicorn pillow

# Run the application
python app.py
```

The application will be available at `http://localhost:5000` with sample data pre-loaded.

### Using Docker (Optional)
```bash
# Build the Docker image
docker build -t wisenews .

# Run the container
docker run -p 5000:5000 wisenews
```

## 📚 API Documentation

WiseNews provides a comprehensive REST API for accessing articles and platform data.

### Base URL
- **Local**: `http://localhost:5000/api`
- **Production**: `https://wisenews-app.onrender.com/api`

### Available Endpoints

#### Health Check
```http
GET /api/status
```
Returns API status and platform information.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "message": "WiseNews API is running",
  "timestamp": "2025-01-05T10:30:00Z",
  "uptime": "2 hours, 15 minutes"
}
```

#### Get All Articles
```http
GET /api/articles
```
Returns all articles with metadata.

**Query Parameters:**
- `category` (optional): Filter by category
- `limit` (optional): Limit number of results

**Response:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "content": "Article content...",
      "author": "Author Name",
      "category": "Technology",
      "published_date": "2025-01-05T10:00:00Z"
    }
  ],
  "total": 15,
  "count": 15
}
```

#### Get Single Article
```http
GET /api/articles/{id}
```
Returns a specific article by ID.

#### Get Categories
```http
GET /api/categories
```
Returns all available categories with article counts.

**Response:**
```json
{
  "categories": [
    {"name": "Technology", "count": 5},
    {"name": "Features", "count": 4},
    {"name": "Guide", "count": 3},
    {"name": "Updates", "count": 3}
  ],
  "total_categories": 4
}
```

#### Search Articles
```http
GET /api/search?q={query}
```
Search articles by keyword.

**Query Parameters:**
- `q` (required): Search query
- `category` (optional): Filter by category

### API Usage Examples

#### cURL Examples
```bash
# Get API status
curl https://wisenews-app.onrender.com/api/status

# Get all articles
curl https://wisenews-app.onrender.com/api/articles

# Search articles
curl "https://wisenews-app.onrender.com/api/search?q=technology"

# Get articles by category
curl "https://wisenews-app.onrender.com/api/articles?category=Technology"
```

#### Python Example
```python
import requests

# Get all articles
response = requests.get('https://wisenews-app.onrender.com/api/articles')
articles = response.json()

# Search for articles
search_response = requests.get('https://wisenews-app.onrender.com/api/search', 
                              params={'q': 'technology'})
search_results = search_response.json()
```

#### JavaScript Example
```javascript
// Get all articles
fetch('https://wisenews-app.onrender.com/api/articles')
  .then(response => response.json())
  .then(data => console.log(data));

// Search articles
fetch('https://wisenews-app.onrender.com/api/search?q=technology')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🚀 Deployment

### Deploy to Render.com (Recommended)

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render.com](https://render.com)

3. **Connect your GitHub repository**

4. **Configure the service:**
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Python Version**: 3.11.5

5. **Deploy**: Render will automatically deploy your application

### Deploy to Heroku

1. **Install Heroku CLI**

2. **Login and create app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

### Deploy to Railway

1. **Connect GitHub repository** to [Railway.app](https://railway.app)

2. **Configure environment**: Python

3. **Deploy**: Railway will auto-detect and deploy

### Environment Variables

For production deployments, you may want to set:

- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`
- `DATABASE_URL=your-database-url` (if using external database)

## 🎨 Features Detailed

### Article Management
- **Rich Content**: Full-text articles with metadata
- **Categories**: Organized into Technology, Features, Guide, Updates
- **Authors**: Author attribution and information
- **Timestamps**: Published dates and times
- **Content Preview**: Automatic excerpt generation

### Search & Discovery
- **Full-Text Search**: Search across titles, content, and authors
- **Category Filtering**: Filter results by category
- **Search Highlighting**: Highlighted search terms in results
- **Search Suggestions**: Intelligent search suggestions
- **Related Articles**: Automatic related article suggestions

### User Interface
- **Responsive Design**: Mobile-first, works on all devices
- **Modern Styling**: Beautiful Bootstrap 5 design
- **Smooth Animations**: CSS transitions and hover effects
- **Dark/Light Theme**: Automatic theme adaptation
- **Accessibility**: WCAG compliant design

### Performance
- **Fast Loading**: Optimized for speed
- **Efficient Database**: SQLite with optimized queries
- **Caching**: Browser and server-side caching
- **Compression**: Gzip compression for assets
- **CDN Ready**: Static assets can be served from CDN

## 📁 Project Structure

```
wisenews/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version specification
├── Procfile              # Deployment configuration
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── articles.html     # Articles listing
│   ├── article_detail.html # Single article view
│   ├── category.html     # Category pages
│   ├── search.html       # Search results
│   ├── about.html        # About page
│   └── contact.html      # Contact page
└── static/              # Static assets (CSS, JS, images)
    └── (auto-generated)
```

## 🤝 Contributing

We welcome contributions to WiseNews! Here's how you can help:

### Getting Started
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes locally
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines for Python code
- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Ensure responsive design for UI changes

### Areas for Contribution
- **New Features**: RSS feed integration, user accounts, bookmarking
- **UI/UX Improvements**: Design enhancements, accessibility improvements
- **Performance**: Database optimizations, caching improvements
- **API Enhancements**: New endpoints, improved documentation
- **Testing**: Unit tests, integration tests
- **Documentation**: Tutorials, examples, API documentation

## 📊 Technical Specifications

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLite (production-ready)
- **Server**: Gunicorn WSGI server
- **Python**: 3.11+ required

### Frontend
- **CSS Framework**: Bootstrap 5.1.3
- **Icons**: Font Awesome 6.0.0
- **JavaScript**: Vanilla JS (no frameworks)
- **Responsive**: Mobile-first design

### Performance
- **Load Time**: < 2 seconds
- **Database**: Optimized queries with indexing
- **Caching**: Browser and server-side caching
- **Compression**: Gzip compression enabled

## 🔧 Configuration

### Environment Variables

```bash
# Optional environment variables
FLASK_ENV=production          # Set to 'development' for debug mode
SECRET_KEY=your-secret-key    # For session security
DATABASE_URL=sqlite:///news.db # Database connection string
PORT=5000                     # Port number (default: 5000)
```

### Database Configuration

The application uses SQLite by default, which is perfect for small to medium applications. For larger deployments, you can easily switch to PostgreSQL or MySQL by updating the database URL.

## 📈 Monitoring & Analytics

### Built-in Monitoring
- Health check endpoint (`/api/status`)
- Error logging and handling
- Performance metrics tracking
- Uptime monitoring

### External Monitoring
The application is compatible with monitoring services like:
- New Relic
- DataDog
- Sentry (for error tracking)
- Google Analytics (frontend)

## 🔒 Security Features

- **Input Validation**: All user inputs are validated and sanitized
- **SQL Injection Protection**: Using SQLAlchemy ORM
- **XSS Protection**: Template auto-escaping enabled
- **CSRF Protection**: Form validation tokens
- **Security Headers**: Proper HTTP security headers
- **Rate Limiting**: API rate limiting capabilities

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 WiseNews

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **Flask**: The web framework that powers WiseNews
- **Bootstrap**: For the beautiful, responsive UI components
- **Font Awesome**: For the comprehensive icon library
- **Render.com**: For reliable, free hosting
- **GitHub**: For version control and collaboration tools

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline code comments
- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

### Contact Information
- **Website**: [https://wisenews-app.onrender.com](https://wisenews-app.onrender.com)
- **API Documentation**: [https://wisenews-app.onrender.com/api/status](https://wisenews-app.onrender.com/api/status)
- **GitHub**: [https://github.com/yourusername/wisenews](https://github.com/yourusername/wisenews)

---

**Built with ❤️ by the WiseNews Team**

*WiseNews - Your Intelligent News Platform*
