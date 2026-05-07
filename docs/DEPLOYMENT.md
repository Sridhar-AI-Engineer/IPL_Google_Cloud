# IPL Agentic Coach - Production Deployment Guide v2.0

## 📋 Pre-Deployment Checklist

- [ ] All tests passing (`pytest`)
- [ ] Code linted and formatted (`black`, `flake8`, `mypy`)
- [ ] Security scanning passed (`bandit`)
- [ ] Database migrations reviewed
- [ ] Environment variables configured
- [ ] Docker image built and tested
- [ ] Docker Compose tested locally
- [ ] Monitoring configured (Prometheus, Grafana)
- [ ] Error tracking configured (Sentry)
- [ ] Backup strategy in place
- [ ] SSL/TLS certificates ready
- [ ] Load balancer configured

---

## 🚀 Quick Start (Docker Compose)

### 1. **Clone Repository**
```bash
git clone <repo-url>
cd IPL_Google_Cloud
```

### 2. **Create .env File**
```bash
cp .env.example .env
```

Edit `.env` with production values:
```env
ENV=production
DEBUG=false
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DATABASE_URL=postgresql+psycopg2://ipl_user:your_password@postgres:5432/ipl_agentic_coach
REDIS_URL=redis://redis:6379/0
REDIS_ENABLED=true
GEMINI_API_KEY=<your-gemini-key>
SENTRY_DSN=<your-sentry-dsn>
```

### 3. **Build Docker Image**
```bash
docker build -t ipl-agentic-coach:latest .
```

### 4. **Start Services**
```bash
docker-compose up -d
```

Verify services:
```bash
docker-compose ps
docker logs ipl-app
```

### 5. **Access Application**
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **pgAdmin**: http://localhost:5050 (admin@ipl.com/admin)
- **Prometheus**: http://localhost:9090

---

## 🗄️ Database Setup

### PostgreSQL Migration

```bash
# Run migrations with Alembic (when available)
docker exec ipl-app alembic upgrade head

# Or manually create tables
docker exec ipl-app python -c "
from ipl_agentic_coach.backend.app import models, database
models.Base.metadata.create_all(bind=database.engine)
"
```

### Create Superuser (Admin)

```bash
docker exec ipl-app python -c "
from ipl_agentic_coach.backend.app import crud, database, schemas
db = database.SessionLocal()
crud.create_user(db, schemas.UserCreate(username='admin', email='admin@ipl.com'))
db.close()
"
```

---

## 🔐 Security Configuration

### 1. **JWT Secrets**
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. **CORS Settings**
Update in `.env`:
```env
CORS_ORIGINS=https://yourfrontend.com,https://app.yourfrontend.com
```

### 3. **HTTPS/SSL**
```bash
# Using Nginx as reverse proxy with SSL
docker run -d \
  -p 443:443 \
  -v /path/to/cert:/etc/nginx/certs:ro \
  -v ./nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:latest
```

### 4. **Rate Limiting**
Enabled by default. Adjust in `.env`:
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600
```

---

## 📊 Monitoring & Observability

### Prometheus Scrape Config
Already configured in `prometheus.yml`. Add custom dashboards:

```bash
# Access Prometheus UI
http://localhost:9090

# Query metrics
ipl_requests_total
ipl_request_duration_seconds
ipl_decisions_submitted_total
```

### Grafana Dashboards

1. Go to http://localhost:3000
2. Add Prometheus data source: `http://prometheus:9090`
3. Create dashboards:
   - Request rate (ipl_requests_total)
   - Response latency (ipl_request_duration_seconds)
   - Decisions submitted (ipl_decisions_submitted_total)
   - Error rate (ipl_requests_total with status >= 400)

### Sentry Integration

```env
SENTRY_ENABLED=true
SENTRY_DSN=https://<key>@sentry.io/<project>
```

Visit Sentry dashboard to monitor errors in real-time.

---

## 🔄 Scaling & Performance

### Horizontal Scaling

```bash
# Deploy multiple app instances behind load balancer
docker-compose scale app=4
```

### Connection Pooling
```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600
```

### Caching (Redis)
```env
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0
```

### Database Indexing
```sql
-- Create indexes
CREATE INDEX idx_user_points ON users(points DESC);
CREATE INDEX idx_decision_score ON decisions(score);
CREATE INDEX idx_decision_user ON decisions(user_id);
CREATE INDEX idx_decision_timestamp ON decisions(timestamp);
```

---

## 🛠️ Maintenance

### Backup Database

```bash
# Daily backup to S3
docker exec ipl-postgres pg_dump -U ipl_user ipl_agentic_coach | \
  aws s3 cp - s3://your-bucket/backups/ipl-$(date +%Y%m%d).sql.gz
```

### Log Rotation
```bash
# Logs are JSON formatted in ./logs/app.log
# Use logrotate for rotation:
docker volume ls
docker exec ipl-app logrotate /etc/logrotate.d/app
```

### Health Checks
```bash
# Check app health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/ready

# Check liveness
curl http://localhost:8000/alive
```

---

## 🚨 Troubleshooting

### App Won't Start
```bash
docker logs ipl-app
# Check for database connection errors
# Verify DATABASE_URL in .env
```

### PostgreSQL Connection Timeout
```bash
docker exec ipl-postgres psql -U ipl_user -d ipl_agentic_coach -c "\dt"
# Verify postgres is healthy
docker ps | grep ipl-postgres
```

### High Memory Usage
```bash
# Check memory consumption
docker stats

# Adjust in docker-compose.yml:
# mem_limit: 1g
# memswap_limit: 2g
```

### Redis Connection Issues
```bash
docker exec ipl-redis redis-cli ping
# Should return: PONG
```

---

## 📈 Performance Tuning

### Database Query Optimization
```python
# Use query indexing
db.query(models.Decision).filter(
    models.Decision.score > 0.7
).options(joinedload(models.Decision.user))
```

### API Response Caching
```env
# Cache leaderboard for 5 minutes
# Implemented via Redis
```

### Request Compression
```python
# Gzip compression enabled by default
# Minimum size: 500 bytes
```

---

## 📱 API Endpoints

### Public Endpoints
- `GET /` - Homepage
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token

### User Endpoints
- `POST /users/create` - Create user
- `GET /users/` - List users
- `GET /users/{id}` - Get user
- `GET /users/leaderboard/top` - Get leaderboard

### Decision Endpoints
- `POST /decisions/submit` - Submit decision
- `POST /decisions/evaluate` - Evaluate decision
- `GET /decisions/` - List decisions
- `GET /decisions/{id}` - Get decision

### Admin Endpoints
- `GET /admin/dashboard/stats` - Dashboard stats
- `GET /admin/users` - List all users
- `POST /admin/users/{id}/ban` - Ban user
- `POST /admin/users/{id}/reset-points` - Reset points

### Analytics Endpoints
- `GET /analytics/leaderboard-chart` - Leaderboard chart
- `GET /analytics/score-distribution` - Score distribution
- `GET /analytics/score-timeline` - Score timeline
- `GET /analytics/bowler-chart` - Bowler stats
- `GET /analytics/field-heatmap` - Field effectiveness
- `GET /analytics/strategy-breakdown` - Strategy distribution

### Export Endpoints
- `GET /export/decisions/csv` - Export to CSV
- `GET /export/decisions/json` - Export to JSON
- `GET /export/users/csv` - Export users
- `GET /export/leaderboard/csv` - Export leaderboard

---

## 🔄 Continuous Deployment (GitHub Actions)

The CI/CD pipeline automatically:

1. **Runs tests** on every push
2. **Lints code** (flake8, black, mypy)
3. **Scans for security** issues (bandit)
4. **Builds Docker image**
5. **Pushes to registry** (ghcr.io)
6. **Deploys to production** (on main branch)

Push to deploy:
```bash
git push origin main
```

Watch deployment progress:
```bash
# GitHub Actions tab in repo
```

---

## 📞 Support & Resources

- **Documentation**: [docs/](../docs/)
- **API Docs**: http://your-app:8000/api/docs
- **Monitoring**: http://your-app:3000 (Grafana)
- **Issues**: GitHub Issues
- **Status**: Statuspage.io (coming soon)

---

## 🎯 Deployment Checklist (Final)

Before going live:

- [ ] Domain name configured
- [ ] SSL certificate installed
- [ ] Database backups automated
- [ ] Monitoring dashboards created
- [ ] Error tracking working
- [ ] Load testing completed (>1000 users/sec)
- [ ] Disaster recovery plan documented
- [ ] Runbooks created for common issues
- [ ] Team trained on operations
- [ ] Documentation reviewed

---

**Version**: 2.0.0
**Last Updated**: May 7, 2026
**Status**: Production Ready ✅
