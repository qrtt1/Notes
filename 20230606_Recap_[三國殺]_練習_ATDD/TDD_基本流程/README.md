# Recap [三國殺] 練習 ATDD/TDD 基本流程

1. 許願
2. 實現願望

## 開始遊戲 create_game

情境：我們「想像」大平台會跟我們說建立的遊戲 id 與 player 的 id。遊戲開始後，我們可以知道場上有哪些玩家。

### 願望內容

POST /api/games
Request Body:

```json
{
  "gameId": "my-id",
  "players": [
    {
      "id": "player-a"
    },
    {
      "id": "player-b"
    },
    {
      "id": "player-c"
    },
    {
      "id": "player-d"
    }
  ]
}
```

Response Body: 同上。

### 實現願望

1. 實作對應的 controller，並簡單地 hardcode response 讓測試過關
2. 開始實作對應的 GameDto 與 PlayerDto，接上 Request Body 的內容
3. 試著修改 test case，確定實作會隨著 input data 變化
4. 開始做 repository 與 Domain model：Game 與 Player
5. 實作 Domain model 與 DTO 的轉換
6. 做一個 find-the-game 確定 Game 的資料有正確保存

## 指定玩家角色 assignRoles

情境：遊戲開始到玩家可以動作前，系統要替玩家隨機指派角色。

### 願望內容

> 修改願望，一樣的 Request 進去，但回來時要多出被指派的角色



POST /api/games
Request Body:

```json
{
  "gameId": "my-id",
  "players": [
    {
      "id": "player-a"
    },
    {
      "id": "player-b"
    },
    {
      "id": "player-c"
    },
    {
      "id": "player-d"
    }
  ]
}
```

Response Body:

```json
{
  "gameId": "my-id",
  "players": [
    {
      "id": "player-a",
      "role": "Monarch"
    },
    {
      "id": "player-b",
      "role": "Minister"
    },
    {
      "id": "player-c",
      "role": "Rebel"
    },
    {
      "id": "player-d",
      "role": "Traitor"
    }
  ]
}
```

### 實現願望

做法大同小異：

1. 先將角色 hardcode 到 4 個玩家身上
2. 在 hardcode 的邏輯達到測試綠燈的情況下，開始加入實際的分派角色類別
3. ...etc

***

## 後續的練習與實作

1. 試著將 happy path 路線擴展到每一位玩家，出過一次牌 (或一個動作)。
2. 完成 happy path 後，參考 OOA 與 Example Mapping 用 TDD 的方式細修 Domain Model。

### Item 1

這部分的內容，主要透過先前的「許願」練習就能達成，因為大家都參與了 Event Storming 在流程上不太會有大問題。會缺少的經驗是在「測試期」注入「預先控制好的角色或牌組」，但在變 production 前，永遠只有測試版的也沒什麼關係。

### Item 2

因為昨天是「小步快跑」總體進展不大，還沒有用到 OOA 與 Example Mapping 的產出，在 Happy Path 推展到一個階段。不用完成的 ATDD 推完，就可以分工去細修 Domain Model。
