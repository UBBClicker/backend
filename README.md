# UBBClicker API - Dokumentacja

## Spis treści
1. [Informacje ogólne](#informacje-ogólne)
2. [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
3. [Endpoints API](#endpoints-api)
   - [Użytkownik](#użytkownik)
   - [Gra](#gra)
   - [Przedmioty](#przedmioty)
4. [Autoryzacja](#autoryzacja)
5. [WebSocket](#websocket)
6. [Testy](#testy)

## Informacje ogólne

UBBClicker to backend API dla gry typu clicker. Aplikacja została zbudowana przy użyciu FastAPI i SQLite. API obsługuje:
- Rejestrację i logowanie użytkowników
- Zarządzanie stanem gry (punkty, kliknięcia)
- Zakup i zarządzanie przedmiotami
- Komunikację w czasie rzeczywistym przez WebSocket
- System rankingowy (leaderboard)

## Instalacja i uruchomienie

### Wymagania
- Python 3.11+
- Pakiety wymienione w `requirements.txt`

### Kroki instalacji

1. Sklonuj repozytorium
2. Utwórz wirtualne środowisko:
   ```
   python -m venv venv
   ```
3. Aktywuj wirtualne środowisko:
   - Windows: `venv\Scripts\activate`
   - Linux/MacOS: `source venv/bin/activate`
4. Zainstaluj zależności:
   ```
   pip install -r requirements.txt
   ```
5. Skopiuj `template.env` do `.env` i dostosuj ustawienia
6. Uruchom aplikację:
   ```
   python main.py
   ```

API będzie dostępne pod adresem: `http://localhost:3001`

## Endpoints API

### Użytkownik

#### Rejestracja użytkownika
- **URL:** `/user/register`
- **Metoda:** `POST`
- **Format danych:** JSON
- **Dane wejściowe:**
  ```json
  {
    "nickname": "nazwa_użytkownika",
    "password": "hasło_użytkownika"
  }
  ```
- **Odpowiedź:**
  ```json
  {
    "id": 1,
    "nickname": "nazwa_użytkownika"
  }
  ```

#### Logowanie użytkownika
- **URL:** `/user/login`
- **Metoda:** `POST`
- **Format danych:** `application/x-www-form-urlencoded` (nie JSON!)
- **Dane wejściowe:**
  ```
  username=nazwa_użytkownika&password=hasło_użytkownika
  ```
- **Odpowiedź:**
  ```json
  {
    "access_token": "JWT_TOKEN",
    "token_type": "bearer"
  }
  ```

#### Odświeżanie tokenu
- **URL:** `/user/refresh-token`
- **Metoda:** `POST`
- **Format danych:** Brak (token przesyłany w nagłówku)
- **Nagłówek:** `Authorization: Bearer <twój_aktualny_token>`
- **Odpowiedź:**
  ```json
  {
    "access_token": "NOWY_JWT_TOKEN",
    "token_type": "bearer"
  }
  ```

#### Dane bieżącego użytkownika
- **URL:** `/user/me`
- **Metoda:** `GET`
- **Nagłówek:** `Authorization: Bearer <token>`
- **Odpowiedź:**
  ```json
  {
    "id": 1,
    "nickname": "nazwa_użytkownika"
  }
  ```

### Gra

#### Stan gry
- **URL:** `/game/state`
- **Metoda:** `GET`
- **Nagłówek:** `Authorization: Bearer <token>`
- **Odpowiedź:**
  ```json
  {
    "points": 100,
    "lifetime_points": 150,
    "clicks": 50,
    "points_per_click": 1.0,
    "points_per_second": 0.5
  }
  ```

#### Stan gry z przedmiotami
- **URL:** `/game/state/with-items`
- **Metoda:** `GET`
- **Nagłówek:** `Authorization: Bearer <token>`
- **Odpowiedź:** Stan gry + lista dostępnych przedmiotów z aktualnymi cenami

#### Kliknięcie
- **URL:** `/game/click`
- **Metoda:** `POST`
- **Nagłówek:** `Authorization: Bearer <token>`
- **Odpowiedź:**
  ```json
  {
    "points_earned": 1.0,
    "new_total": 101,
    "lifetime_points": 151,
    "clicks": 51
  }
  ```

#### Zakup przedmiotu
- **URL:** `/game/buy/{item_id}`
- **Metoda:** `POST`
- **Nagłówek:** `Authorization: Bearer <token>`
- **Odpowiedź:**
  ```json
  {
    "success": true,
    "message": "Successfully purchased Item Name",
    "new_points": 90,
    "new_points_per_click": 1.5,
    "new_points_per_second": 0.6,
    "item_quantity": 1,
    "item_cost": 12
  }
  ```

#### Tablica wyników
- **URL:** `/game/leaderboard`
- **Metoda:** `GET`
- **Parametry:** `?limit=10` (opcjonalnie)
- **Odpowiedź:** Lista najlepszych graczy według zdobytych punktów lifetime

### Przedmioty

#### Lista wszystkich przedmiotów
- **URL:** `/items/`
- **Metoda:** `GET`
- **Odpowiedź:** Lista wszystkich dostępnych przedmiotów

#### Pojedynczy przedmiot
- **URL:** `/items/{item_id}`
- **Metoda:** `GET`
- **Odpowiedź:** Szczegóły pojedynczego przedmiotu

#### Przedmioty użytkownika
- **URL:** `/items/user/{user_id}`
- **Metoda:** `GET`
- **Nagłówek:** `Authorization: Bearer <token>`
- **Odpowiedź:** Lista przedmiotów posiadanych przez użytkownika

## Autoryzacja

### Implementacja po stronie klienta

1. **Logowanie:**
   ```javascript
   async function login(nickname, password) {
     const formData = new URLSearchParams();
     formData.append('username', nickname);
     formData.append('password', password);
     
     const response = await fetch('/user/login', {
       method: 'POST',
       headers: {
         'Content-Type': 'application/x-www-form-urlencoded'
       },
       body: formData
     });
     
     const data = await response.json();
     if (response.ok) {
       // Zapisz token w bezpiecznym miejscu (localStorage, secure cookie)
       localStorage.setItem('token', data.access_token);
       return true;
     }
     return false;
   }
   ```

2. **Dodawanie tokenu do zapytań:**
   ```javascript
   function getAuthHeaders() {
     const token = localStorage.getItem('token');
     return {
       'Authorization': `Bearer ${token}`,
       'Content-Type': 'application/json'
     };
   }
   
   async function fetchProtectedResource(url) {
     const response = await fetch(url, {
       headers: getAuthHeaders()
     });
     
     if (response.status === 401) {
       // Token wygasł, spróbuj go odświeżyć
       const refreshed = await refreshToken();
       if (refreshed) {
         // Ponów zapytanie
         return fetch(url, { headers: getAuthHeaders() });
       } else {
         // Przekieruj do strony logowania
         redirectToLogin();
       }
     }
     
     return response;
   }
   ```

3. **Odświeżanie tokenu:**
   ```javascript
   async function refreshToken() {
     const token = localStorage.getItem('token');
     
     if (!token) return false;
     
     try {
       const response = await fetch('/user/refresh-token', {
         method: 'POST',
         headers: {
           'Authorization': `Bearer ${token}`
         }
       });
       
       if (response.ok) {
         const data = await response.json();
         localStorage.setItem('token', data.access_token);
         return true;
       }
       return false;
     } catch (error) {
       console.error('Token refresh failed:', error);
       return false;
     }
   }
   ```

### Ważne informacje dotyczące tokenu

- Token wygasa po 15 minutach nieaktywności
- Zaleca się odświeżanie tokenu przed każdą ważną operacją lub implementację mechanizmu automatycznego odświeżania
- Po wygaśnięciu tokenu konieczne jest ponowne logowanie
- Implementacja po stronie klienta powinna obsługiwać błędy 401 (Unauthorized) przez próbę odświeżenia tokenu, a następnie ponowne wykonanie oryginalnego żądania

## WebSocket

### Nawiązywanie połączenia WebSocket

```javascript
function connectWebSocket() {
  const token = localStorage.getItem('token');
  
  if (!token) {
    console.error('No token available for WebSocket connection');
    return null;
  }
  
  const ws = new WebSocket(`ws://localhost:3001/game/ws/${token}`);
  
  ws.onopen = () => {
    console.log('WebSocket connection established');
    // Możesz od razu poprosić o aktualny stan gry
    ws.send(JSON.stringify({ type: 'get_state' }));
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'game_state':
        updateGameState(message.data);
        break;
      case 'click_result':
        updateAfterClick(message.data);
        break;
      case 'purchase_result':
        updateAfterPurchase(message.data);
        break;
      case 'items_list':
        updateItemsList(message.data);
        break;
      case 'leaderboard_update':
        updateLeaderboard(message.data);
        break;
    }
  };
  
  ws.onclose = () => {
    console.log('WebSocket connection closed');
    // Spróbuj ponownie połączyć po pewnym czasie
    setTimeout(connectWebSocket, 5000);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return ws;
}
```

### Wysyłanie zdarzeń przez WebSocket

```javascript
// Wysyłanie kliknięcia
function sendClick(ws) {
  ws.send(JSON.stringify({ type: 'click' }));
}

// Zakup przedmiotu
function buyItem(ws, itemId) {
  ws.send(JSON.stringify({ 
    type: 'buy_item',
    item_id: itemId
  }));
}

// Pobieranie listy przedmiotów
function getItems(ws) {
  ws.send(JSON.stringify({ type: 'get_items' }));
}

// Pobieranie aktualnego stanu gry
function getGameState(ws) {
  ws.send(JSON.stringify({ type: 'get_state' }));
}
```

## Testy

Projekt zawiera testy jednostkowe dla wszystkich głównych funkcjonalności. Aby uruchomić testy:

```
python run_tests.py
```

Testy sprawdzają:
- Rejestrację i logowanie użytkowników
- Podstawowe mechaniki gry (kliknięcia, pasywne generowanie punktów)
- System zakupu przedmiotów
- Tablicę wyników

**Uwaga:** W obecnej wersji nie ma testów dla endpointu odświeżania tokenów.