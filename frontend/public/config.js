// Runtime configuration - update this URL after deploying the backend
// This file is served as-is and NOT processed by webpack/React
// Replace the API_BASE value with your actual backend URL after deployment
window.APP_CONFIG = {
  API_BASE: '__BACKEND_API_URL__'
};
// For local development, set API_BASE to: 'http://localhost:8000'
// For production, set API_BASE to your ALB/AgentCore URL, e.g.:
// API_BASE: 'http://vacation-planner-api-alb-xxxxx.us-west-2.elb.amazonaws.com'
