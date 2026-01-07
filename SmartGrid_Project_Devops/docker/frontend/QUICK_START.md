# Quick Start - Frontend Fix

## 🔧 Si të Fixosh Connection Issues

### Step 1: Rebuild Frontend Container
```bash
cd SmartGrid_Project_Devops/docker
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Step 2: Check Logs
```bash
docker logs -f smartgrid-frontend
```

### Step 3: Test Connection
```bash
# Test në terminal
curl http://localhost:8080

# Ose hap në browser
open http://localhost:8080
```

### Step 4: Check Port
```bash
# Kontrollo nëse porti është i hapur
lsof -i :8080

# Nëse porti është i zënë, ndrysho në docker-compose.yml
```

## ✅ Expected Output

Kur frontend është running, duhet të shohësh:
- Login form
- CSS dhe JS files të ngarkuara
- No errors në browser console

## 🐛 Common Issues

### Issue 1: Port Already in Use
**Solution**: Ndrysho port në docker-compose.yml:
```yaml
ports:
  - "8081:8080"  # Ndrysho 8080 në 8081
```

### Issue 2: Container Not Starting
**Solution**: 
```bash
docker-compose logs frontend
# Shiko errors dhe fix them
```

### Issue 3: Static Files Not Loading
**Solution**: 
```bash
# Rebuild me --no-cache
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Issue 4: 404 Errors
**Solution**: Kontrollo që file paths janë të sakta:
- `/static/css/simple-style.css` ✅
- `/static/js/dashboard-main.js` ✅

## 📝 Verification Checklist

- [ ] Container është running: `docker ps | grep frontend`
- [ ] Porti është i hapur: `lsof -i :8080`
- [ ] Logs nuk tregojnë errors: `docker logs frontend`
- [ ] Browser console nuk ka errors (F12)
- [ ] CSS file ngarkohet: Check Network tab
- [ ] JS file ngarkohet: Check Network tab
