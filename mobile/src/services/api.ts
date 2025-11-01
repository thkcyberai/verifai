import axios from 'axios';
import { API_URL } from '../config/constants';

export interface VerifyRequest {
  claim: string;
  language?: string;
  media_url?: string;
}

export interface VerificationResult {
  id: string;
  claim: string;
  verdict: 'TRUE' | 'FALSE' | 'MISLEADING' | 'UNVERIFIED' | 'NEEDS_CONTEXT';
  confidence: number;
  evidence: Evidence[];
  reasoning: string;
  sources: Source[];
  media_analysis?: MediaAnalysis;
  created_at: string;
}

export interface Evidence {
  source: string;
  title: string;
  snippet: string;
  url: string;
  relevance_score: number;
}

export interface Source {
  url: string;
  title: string;
  credibility: number;
}

export interface MediaAnalysis {
  is_manipulated: boolean;
  confidence: number;
  findings: string[];
}

class APIService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_URL;
  }

  async verify(request: VerifyRequest): Promise<VerificationResult> {
    try {
      const response = await axios.post(`${this.baseURL}/verify`, request, {
        timeout: 30000, // 30 second timeout
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new Error(error.response.data.detail || 'Verification failed');
      } else if (error.request) {
        throw new Error('Network error - please check your connection');
      } else {
        throw new Error('Failed to verify claim');
      }
    }
  }

  async getClaimStatus(claimId: string): Promise<{ status: string; result?: VerificationResult }> {
    try {
      const response = await axios.get(`${this.baseURL}/claims/${claimId}/status`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get claim status');
    }
  }

  async getClaim(claimId: string): Promise<VerificationResult> {
    try {
      const response = await axios.get(`${this.baseURL}/claims/${claimId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get claim');
    }
  }

  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await axios.get(`${this.baseURL}/health`);
      return response.data;
    } catch (error) {
      throw new Error('Backend is not responding');
    }
  }
}

export const apiService = new APIService();
