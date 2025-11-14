/**
 * Apollo Client Configuration (PDCA #27)
 *
 * Example configuration for React frontend.
 */

import { ApolloClient, InMemoryCache, createHttpLink, ApolloLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

// HTTP link to GraphQL endpoint
const httpLink = createHttpLink({
  uri: 'http://localhost:8000/graphql',
});

// Auth link to add JWT token to requests
const authLink = setContext((_, { headers }) => {
  // Get token from localStorage
  const token = localStorage.getItem('access_token');

  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  };
});

// Create Apollo Client
export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          // Cache policy for site query
          site: {
            read(existing, { args, toReference }) {
              return existing || toReference({
                __typename: 'Site',
                id: args?.id,
              });
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});


/**
 * GraphQL Queries
 */

import { gql } from '@apollo/client';

// Executive Dashboard Query (replaces 8+ REST requests!)
export const EXECUTIVE_DASHBOARD_QUERY = gql`
  query ExecutiveDashboard($siteId: Int!, $periodDays: Int) {
    currentUser {
      id
      email
      fullName
      role
    }
    site(id: $siteId, periodDays: $periodDays) {
      id
      name
      location
      dashboard360 {
        overallHealthScore {
          score
          status
          color
        }
        maintenance {
          averageHealth
          criticalAssets
          criticalAlarms
          highAlarms
        }
        operations {
          efficiencyScore
          berthUtilization
        }
      }
      roi {
        totalSavings
        annualProjection
        roiPercentage
        predictiveMaintenance {
          failuresPrevented
          emergencyCostsAvoided
          savings
        }
      }
      assets(limit: 10) {
        id
        name
        type
        status
        health
        location
      }
      alarms(limit: 5) {
        id
        message
        severity
        timestamp
        acknowledged
      }
    }
  }
`;

// Assets Query with Filtering
export const ASSETS_QUERY = gql`
  query Assets($siteId: Int!, $filter: AssetFilter) {
    assets(siteId: $siteId, filter: $filter) {
      id
      name
      type
      status
      health
      location
      lastMaintenance
    }
  }
`;

// Alarms Query with Filtering
export const ALARMS_QUERY = gql`
  query Alarms($siteId: Int!, $filter: AlarmFilter) {
    alarms(siteId: $siteId, filter: $filter) {
      id
      message
      severity
      assetId
      timestamp
      acknowledged
    }
  }
`;

// Gateways Query
export const GATEWAYS_QUERY = gql`
  query Gateways {
    gateways {
      id
      name
      status
      connectedTags
      protocol
    }
  }
`;


/**
 * GraphQL Mutations
 */

// Update Asset Mutation
export const UPDATE_ASSET_MUTATION = gql`
  mutation UpdateAsset($input: UpdateAssetInput!) {
    updateAsset(input: $input) {
      id
      status
      health
    }
  }
`;

// Acknowledge Alarm Mutation
export const ACKNOWLEDGE_ALARM_MUTATION = gql`
  mutation AcknowledgeAlarm($input: AcknowledgeAlarmInput!) {
    acknowledgeAlarm(input: $input) {
      id
      acknowledged
    }
  }
`;


/**
 * TypeScript Types (auto-generated with graphql-codegen)
 */

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: string;
}

export interface OverallHealthScore {
  score: number;
  status: string;
  color: string;
}

export interface MaintenanceMetrics {
  averageHealth: number;
  criticalAssets: number;
  criticalAlarms: number;
  highAlarms: number;
}

export interface OperationsMetrics {
  efficiencyScore: number;
  berthUtilization: number;
}

export interface Dashboard360 {
  overallHealthScore: OverallHealthScore;
  maintenance: MaintenanceMetrics;
  operations: OperationsMetrics;
}

export interface PredictiveMaintenanceROI {
  failuresPrevented: number;
  emergencyCostsAvoided: number;
  savings: number;
}

export interface ROI {
  totalSavings: number;
  annualProjection: number;
  roiPercentage: number;
  predictiveMaintenance: PredictiveMaintenanceROI;
}

export interface Asset {
  id: string;
  name: string;
  type: string;
  status: string;
  health: number;
  location?: string;
  lastMaintenance?: string;
}

export interface Alarm {
  id: string;
  message: string;
  severity: string;
  assetId?: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface Site {
  id: string;
  name: string;
  location: string;
  dashboard360: Dashboard360;
  roi: ROI;
  assets: Asset[];
  alarms: Alarm[];
}

export interface ExecutiveDashboardData {
  currentUser: User;
  site: Site;
}
