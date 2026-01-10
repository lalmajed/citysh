# 🗺️ Riyadh Dynamic Map

A modern, interactive map application for exploring Riyadh locations with a **React** frontend and **Node.js/Express** backend.

![Riyadh Map](https://via.placeholder.com/800x400/1a1a2e/3498db?text=Riyadh+Dynamic+Map)

## 📁 Project Structure

```
riyadh-dynamic-map/
├── frontend/          # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map/          # Leaflet map component
│   │   │   └── Sidebar/      # Location list & search
│   │   ├── services/
│   │   │   └── api.js        # API service layer
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
├── backend/           # Node.js Express API
│   ├── server.js
│   ├── .env
│   └── package.json
├── package.json       # Root package.json
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. **Clone or navigate to the project:**
   ```bash
   cd riyadh-dynamic-map
   ```

2. **Install all dependencies:**
   ```bash
   # Install backend dependencies
   cd backend
   npm install

   # Install frontend dependencies
   cd ../frontend
   npm install
   ```

### Running the Application

You need to run both the backend and frontend servers:

**Terminal 1 - Backend (Port 5000):**
```bash
cd backend
npm start
```

**Terminal 2 - Frontend (Port 3000):**
```bash
cd frontend
npm start
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000/api

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/locations` | Get all locations |
| GET | `/api/locations/:id` | Get location by ID |
| GET | `/api/locations/type/:type` | Get locations by type |
| POST | `/api/locations` | Add new location |
| GET | `/api/search?q=query` | Search locations |
| GET | `/api/bounds` | Get map bounds |
| GET | `/api/health` | Health check |

### Example API Requests

```bash
# Get all locations
curl http://localhost:5000/api/locations

# Search for locations
curl http://localhost:5000/api/search?q=tower

# Add a new location
curl -X POST http://localhost:5000/api/locations \
  -H "Content-Type: application/json" \
  -d '{"name": "New Place", "lat": 24.75, "lng": 46.68, "type": "custom"}'
```

## ✨ Features

- 🗺️ **Interactive Map** - Pan, zoom, and explore Riyadh
- 📍 **Location Markers** - Color-coded by type (landmark, mall, road, district)
- 🔍 **Search** - Filter locations by name
- ➕ **Add Locations** - Add custom markers to the map
- 📱 **Responsive** - Works on desktop and mobile
- 🎨 **Modern UI** - Clean, dark-themed sidebar

## 🛠️ Tech Stack

### Frontend
- React 18
- React-Leaflet (maps)
- Axios (HTTP client)
- CSS3 (styling)

### Backend
- Node.js
- Express.js
- CORS (cross-origin support)
- dotenv (environment variables)

## 📦 Environment Variables

### Backend (.env)
```env
PORT=5000
NODE_ENV=development
```

### Frontend
Create a `.env` file in the frontend folder:
```env
REACT_APP_API_URL=http://localhost:5000/api
```

## 🔧 Customization

### Adding More Locations

Edit `backend/server.js` and add to the `riyadhLocations` array:

```javascript
const riyadhLocations = [
  // Existing locations...
  { id: 6, name: "Your Location", lat: 24.xxx, lng: 46.xxx, type: "custom" },
];
```

### Changing Map Tiles

Edit `frontend/src/components/Map/RiyadhMap.js` and change the TileLayer URL:

```javascript
<TileLayer
  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"  // OpenStreetMap
  // Or use other providers:
  // url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"  // Dark theme
/>
```

## 📄 License

ISC License

---

Made with ❤️ for Riyadh
