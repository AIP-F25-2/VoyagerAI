// API client for VoyagerAI frontend
// Use centralized apiClient for all requests
import { apiClient } from './apiClient';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (typeof window !== 'undefined' ? '' : 'http://localhost:5001');

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface SignupResponse {
  token: string;
  user: User;
}

// Auth API functions
export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Login failed');
  }

  return response.json();
}

export async function signup(name: string, email: string, password: string): Promise<SignupResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Signup failed');
  }

  return response.json();
}

export async function getProfile(token: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/api/auth/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get profile');
  }

  return response.json();
}

export async function verifyToken(token: string): Promise<{ success: boolean; user?: User }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/verify-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    });
    
    if (!response.ok) {
      return { success: false };
    }
    
    const data = await response.json();
    return { success: data.success, user: data.user };
  } catch {
    return { success: false };
  }
}

// Events API functions
export interface Event {
  id: string;
  name: string;
  description: string;
  dates: {
    start: {
      localDate: string;
      localTime: string;
    };
  };
  _embedded: {
    venues: Array<{
      name: string;
      city: {
        name: string;
      };
    }>;
  };
  priceRanges: Array<{
    min: number;
    max: number;
  }>;
  url: string;
  images: Array<{
    url: string;
  }>;
  source: string;
}

export async function getEvents(): Promise<{ csv_events: Event[]; ticketmaster: Event[]; pagination: any }> {
  const response = await fetch(`${API_BASE_URL}/api/events`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }

  return response.json();
}

export async function scrapeEvents(city: string, limit: number = 10): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/scrape`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ city, limit }),
  });

  if (!response.ok) {
    throw new Error('Failed to scrape events');
  }

  return response.json();
}

// Hotels API functions
export interface Hotel {
  id: string;
  name: string;
  city: string;
  address: string;
  location?: string;
  rating?: number;
  review_count?: number;
  price_per_night?: string;
  url?: string;
  check_in?: string;
  check_out?: string;
  guests?: number;
  source: string;
}

export interface HotelSearchResponse {
  success: boolean;
  hotels: Hotel[];
}

export interface HotelListResponse {
  success: boolean;
  hotels: Hotel[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
}

export interface CitiesResponse {
  success: boolean;
  cities: string[];
}

export async function searchHotels(city: string, checkIn?: string, checkOut?: string, guests?: number, limit: number = 10): Promise<HotelSearchResponse> {
  const params = new URLSearchParams({
    city,
    limit: limit.toString(),
  });
  
  if (checkIn) params.append('check_in', checkIn);
  if (checkOut) params.append('check_out', checkOut);
  if (guests) params.append('guests', guests.toString());

  const response = await fetch(`${API_BASE_URL}/api/hotels/search?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to search hotels');
  }

  return response.json();
}

export async function getHotels(city?: string, query?: string, minRating?: number, limit: number = 20, page: number = 1): Promise<HotelListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    page: page.toString(),
  });
  
  if (city) params.append('city', city);
  if (query) params.append('q', query);
  if (minRating) params.append('min_rating', minRating.toString());

  const response = await fetch(`${API_BASE_URL}/api/hotels?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch hotels');
  }

  return response.json();
}

export async function getHotelCities(): Promise<CitiesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/hotels/cities`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch cities');
  }

  return response.json();
}

export async function getPopularHotels(city?: string, limit: number = 10): Promise<HotelSearchResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
  });
  
  if (city) params.append('city', city);

  const response = await fetch(`${API_BASE_URL}/api/hotels/popular?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch popular hotels');
  }

  return response.json();
}

export async function getHotelDetails(hotelId: string): Promise<{ success: boolean; hotel: Hotel }> {
  const response = await fetch(`${API_BASE_URL}/api/hotels/${hotelId}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch hotel details');
  }

  return response.json();
}

// Flights API functions
export interface Flight {
  id: string;
  airline: string;
  origin: string;
  destination: string;
  departure: string;
  arrival: string;
  price: number;
  duration: string;
}

export async function searchFlights(origin: string, destination: string, departureDate: string, returnDate?: string, adults: number = 1, limit: number = 10): Promise<Flight[]> {
  const params = new URLSearchParams({
    origin,
    destination,
    departure_date: departureDate,
    adults: adults.toString(),
    limit: limit.toString(),
  });
  
  if (returnDate) params.append('return_date', returnDate);

  const response = await fetch(`${API_BASE_URL}/api/flights/search?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to search flights');
  }

  return response.json();
}

// Favorites API functions
export interface Favorite {
  id: number;
  user_email: string;
  title: string;
  venue?: string;
  city?: string;
  url?: string;
  image_url?: string;
  provider?: string;
  date?: string;
  time?: string;
  created_at: string;
}

export async function getFavorites(email: string): Promise<Favorite[]> {
  const response = await fetch(`${API_BASE_URL}/api/favorites?email=${encodeURIComponent(email)}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch favorites');
  }

  const data = await response.json();
  return data.favorites || [];
}

export async function addFavorite(favoriteData: {
  email: string;
  title: string;
  venue?: string;
  city?: string;
  url?: string;
  image_url?: string;
  provider?: string;
  date?: string;
  time?: string;
}): Promise<Favorite> {
  const response = await fetch(`${API_BASE_URL}/api/favorites`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(favoriteData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to add favorite');
  }

  const data = await response.json();
  return data.favorite;
}

export async function removeFavorite(favoriteId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/favorites/${favoriteId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to remove favorite');
  }
}
