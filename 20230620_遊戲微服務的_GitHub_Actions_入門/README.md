# 遊戲微服務的 GitHub Actions 入門

隨著遊戲微服務計劃的進展，多數組別可以開始建立 Walking Skeleton，其中一項重要的工作就是將「編譯、測試、部署」的動作自動化，它是典型的 CI/CD 工作的範圍。而各組的原始碼目前以 GitHub 代管為主，我們就能運用 GitHub Actions 簡單實作出 CI/CD Pipeline。

一旦這類的「庶務」被自動化後，這樣特定的工作不會「相依於」特定人士或某位同事的電腦了。

https://youtu.be/RJo7baj6cYM

{%youtube RJo7baj6cYM %}

# 常見的問題

## Q. GitHub Action 的基本結構是什麼呢？

1. 一個 YAML 檔就是在寫一份 Workflow 的內容，一個 Workflow 內有多個 Jobs，而 Jobs 內由多個 Steps 組成
2. 而 Step 中的每一步，就是 `Action`，它可以是別人寫好的，可以複用的 Action，或是任意 Script 的 `run` action

## Q. 我能寫多組 YAML 在 .github/workflows/ 嗎？

可以呦，相當鼓勵讓你的 Workflow 專注它本身的任務。這我們能延續關注點分離來想它，儘量不要讓大腦超載而無法順暢地思考。

在一個遊戲微服務的專案中，通常前端與後端會在一起，那你可能會有這幾個 YAML (workflow)

1. 前端的 CI (build and test)
2. 後端的 CI (build and test)
3. 前後端一起的 CD (build and test and deploy)

或是再另外提供獨立的 Deployment：

1. 前端的 CD (build and test and deploy)
2. 前端的 CD (build and test and deploy)
3. 針對特定 release tag 的 CD

## Q. 分開寫真的好處那麼多嗎？我硬是想合在一起也可以嗎？

1. 全寫在一起理論上做得到，但實務上會很痛苦呦！這樣你就會看像 YAML 像寫程式一樣，一堆的條件判斷在各別的 Step 內。
2. 分開寫除了「用途」「意途」的原因，還有語法上的問題。Workflow 依我們的入門介紹中分為二大區塊： `Listener` 與 `Handler`

我們透過 `Listener` 能控制適當的關注範圍，例如：

1. 針對前端的 CI，只 watch 相關實體路徑 (ex. `frontend/**`) 的 Pull Request 事件
2. 針對後端的 CI，只 watch 相關實體路徑 (ex. `backend/**`) 的 Pull Request 事件
3. 針對前後端的 CD，只 watch 特定的 release branch 的 Push 事件，例如 `release/v0.1`
4. 針對前後端的 CD，只 watch 特定的 release tag 的 Push 事件，例如 `tags/v0.1`
