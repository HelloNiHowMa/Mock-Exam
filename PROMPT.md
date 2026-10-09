# 出題提示詞（給 ChatGPT、Copilot 或其他 AI 用）

使用方式：把下面「===== 從這裡開始複製 =====」以下的全部內容貼給 AI，再附上教材（上傳檔案或貼上文字）。
貼之前，先把【】裡的內容換成你的資料。詳細步驟見「操作說明.md」。

===== 從這裡開始複製 =====

你是【例如：韌體升級流程】的內訓講師，要根據我附上的教材，替【例如：新進 RD】出一份自我檢查用的練習題庫。
題庫會放進一個現成的練習網頁，所以輸出必須是符合下面格式的 JSON。

## 這次的需求

- 練習簿標題：【例如：韌體升級流程練習簿】
- 練習簿代號（id）：【例如：fw-upgrade-101。只能用小寫英文、數字和連字號】
- 題數：【例如：25 題，另外加 10 個縮寫題】
- 圖片：【沒有圖片就刪掉這行。有的話寫：我附了 topo1.png、topo1-blank.png，圖片代號就是檔名去掉副檔名】

## 出題原則

目標是檢查學員是不是真的懂，不是有沒有看過。好題目讓只看過教材的人選錯，想過的人選對。

1. 先讀完教材，列出關鍵概念和新手最常見的誤解，再開始出題。每個錯誤選項都要對應一個真實的誤解。
2. 題型比例：單選約一半，複選和分類各 15% 到 20%，排序和配對合計 10% 到 15%。單選題至少三分之一用情境開頭，例如給 log、現象或兩位同事的不同說法，再問判斷或排查方向。
3. 正確答案不要是最長、最精確的選項。把干擾選項寫得和正確答案一樣具體，有時讓干擾選項最長。不要用「以上皆是」「以上皆非」。
4. 每題都要有解析 e，分兩段，中間用 \n 分開：第一段說明為什麼對、主要的錯誤選項錯在哪；第二段以「容易卡住的地方：」開頭，點出誤解並給一個判斷方法。整段約 100 到 250 字。
5. 把考相似概念、容易搞混的 2 到 4 題綁成易混淆題組（groups），寫一兩句分辨關鍵。
6. 只根據我提供的教材出題，教材沒寫或你不確定的不要出，不要捏造規格編號或參數。
7. 繁體中文、台灣用語、全形標點；專有名詞、指令和參數保留英文原文。不要用 Markdown 語法。

## 格式

輸出一個 JSON 物件，有四個部分：config、questions、abbr、groups。

config：
- id：練習簿代號。title：標題。subtitle：一句話說明給誰用、想檢查什麼。
- mainLabel：選擇題在介面上的名稱，例如「觀念題」。passLine：及格線（%），預設 80。pace：模擬考每題秒數，預設 60。
- aiRole、aiTerms、aiBasis、abbrScope：給網頁上「AI 解析」按鈕用的說明，照範例的語氣填。

questions：每題都有 n（題號，從 1 開始連續、不能重複，最大 999）、q（題目）、e（解析）。依題型再加：
- 單選（不寫 type）：o 是 2 到 6 個選項，a 是正確選項的位置，從 0 開始（0 是第一個）。
- 複選（"type": "multi"）：o 同上，a 是正確選項位置的陣列，例如 [0, 2]。題目註明「（選出所有正確答案）」。
- 分類（"type": "cls"）：items 是所有項目；groups 是各組，每組有標題 t 和格子 s，每格 {"a": 項目位置}。同一個項目最多放一格，沒放的就是干擾項，題目要註明「有 N 個項目用不到」。格子加上 "l": "第 1 站" 這類標籤時，變成逐格判分，適合考流程順序。
- 排序（"type": "order"）：items 照正確順序寫，至少 2 個，不能重複。
- 配對（"type": "match"）：pairs 是至少 2 組 [左, 右]，左右兩欄各自不能重複。
- 有圖時：img 是題目附圖的代號陣列，eimg 是作答後才顯示的解析附圖。沒有圖就不要寫這兩個欄位，解析裡也不要寫「如圖」。
- 選項和項目的順序照正確答案寫就好，網頁會自動打亂。

abbr（縮寫題）：每個 {"cat": 分類, "abbr": 縮寫, "full": 英文全名, "alts": [其他也算對的寫法], "e": 一句說明}。

groups（易混淆題組）：每組 {"name": 名稱, "qs": [題號, …], "key": 分辨關鍵}。

## 輸出要求

- 只輸出 JSON，放在一個 ```json 程式碼區塊裡，前後不要有其他文字。
- JSON 要合法：字串用半形雙引號，字串裡的雙引號寫成 \"，最後一個項目後面不要有逗號。不要出現 </script 這幾個字。
- 題數超過 20 題時分批輸出：第一批輸出完整的 JSON（含 config、abbr、groups，questions 先放前 20 題）；我說「繼續」時，只輸出接下來的題目，格式是用逗號分隔的題目物件（不要外層的中括號），題號接續。

## 範例

下面是格式和品質的標準：六種題型各三題，加上兩組易混淆題組。範例是 5G 領域，只用來示範格式、題型用法和解析寫法；你的題目內容要完全來自我附上的教材。

```json
{
 "config": {
  "id": "example-5gsa",
  "title": "5G SA 協定架構練習簿（範例）",
  "subtitle": "範本示範：六種題型各三題。答案都在架構概念裡，但只靠「看過」選不對，要真的想過才行。",
  "mainLabel": "觀念題",
  "passLine": 80,
  "passNote": "",
  "pace": 60,
  "aiRole": "5G SA 與 O-RAN 協定架構的內訓講師",
  "aiTerms": "協定、介面與訊息名稱保留英文原文",
  "aiBasis": "依 3GPP（TS 38.401、38.470 系列、38.460 系列、38.410 系列、29.281、38.425）與 O-RAN WG4 前傳規格的實際定義說明，著重「哪一層、哪個介面、哪兩個節點之間」",
  "abbrScope": "5G SA／O-RAN 架構"
 },
 "questions": [
  {
   "n": 1,
   "q": "CU-CP 要送一則 RRC 訊息給 UE，這則訊息在 F1-C 上怎麼傳？",
   "o": [
    "包在 F1AP 訊息裡傳給 DU，例如 DL RRC Message Transfer",
    "交給 CU-UP，由 CU-UP 經 F1-U 以 GTP-U 封裝後送到 DU",
    "RRC 是獨立的控制協定，直接放在 SCTP 上送到 DU，不經過 F1AP",
    "包在 F1AP 訊息裡，由 DU 原封不動轉給 RU，再由 RU 經空中介面送給 UE"
   ],
   "a": 0,
   "e": "F1AP 的職責包含「承載與 RRC 傳遞」。RRC 訊息（經過 CU-CP 的 PDCP 處理）放在 F1AP 訊息的 RRC Container 裡；F1AP 在 DU 終止，DU 取出 RRC 後經 RLC、MAC 從空中介面送給 UE，不會把 F1AP 轉給 RU。F1-C 上的 SCTP payload 永遠是 F1AP，RRC 也不走使用者面的 F1-U。\n容易卡住的地方：RRC 也是控制訊息，很容易以為它自己就能跑在 SCTP 上。F1-C 上只有 F1AP 這一種應用協定，其他控制內容都要裝進 F1AP 裡。"
  },
  {
   "n": 2,
   "q": "以 IP 類型的 PDU Session 為例，在 N3 抓到的 GTP-U 封包裡，被封裝在 GTP-U payload 中的「內層 IP」位址代表什麼？",
   "o": [
    "AMF 與 CU-CP 的位址",
    "UE 與它所連線的遠端主機的位址",
    "CU-UP 與 UPF 之間的隧道端點位址",
    "DU 與 CU-UP 的位址"
   ],
   "a": 1,
   "e": "N3 封包由外到內是 Ethernet、外層 IP、UDP、GTP-U（基本標頭與擴充標頭），最裡面才是 UE 的 IP 封包。外層 IP 是隧道端點（CU-UP ↔ UPF），用來在傳輸網路上路由；內層 IP 是使用者封包本身，也就是 UE 和遠端主機。\n容易卡住的地方：同一個封包裡有兩個 IP 標頭。看到 IP 位址時，先確認是外層還是內層，才知道它代表網路設備還是使用者。",
   "img": [
    "n3-blank"
   ],
   "eimg": [
    "n3-full"
   ]
  },
  {
   "n": 3,
   "q": "DU 的 log 顯示與 CU 之間的 SCTP association 已建立，但接著收到 F1 Setup Failure。最合理的排查方向是？",
   "o": [
    "先查 CU 與 DU 之間的 IP 路由和防火牆，確認 F1-C 的 SCTP 埠 38472 沒有被擋",
    "查 RU 的 eCPRI 與前傳 VLAN 設定，因為前傳不通時 F1 Setup 會被拒",
    "把 F1-C 改成走 UDP 重新建立，避開 SCTP association 的問題",
    "看 Failure 的 cause，比對兩端的 PLMN、NR CGI 等小區設定"
   ],
   "a": 3,
   "e": "SCTP 已連上，表示路由和防火牆大致沒問題，傳輸層可以先排除。Setup 被拒是應用層設定不相容，Failure 訊息裡的 cause 值就是 F1AP 告訴你的原因，應該從這裡和雙方的設定參數下手。F1-C 規定走 SCTP，不能改用 UDP；RU 的前傳設定也不影響 F1 Setup，F1AP 根本不經過 RU。\n容易卡住的地方：一看到「連線失敗」就去查網路，是最常見的反射動作。先判斷失敗發生在哪一層，才知道該查網路還是查設定。"
  },
  {
   "n": 4,
   "type": "multi",
   "q": "下列哪些介面的封包裡，會看到 SCTP 標頭？（選出所有正確答案）",
   "o": [
    "N3",
    "Open Fronthaul 的 C-plane",
    "F1-U",
    "E1",
    "F1-C",
    "N2"
   ],
   "a": [
    3,
    4,
    5
   ],
   "e": "SCTP 是 NG、F1、E1 三個控制面共用的傳輸層，所以 N2（NGAP）、E1（E1AP）、F1-C（F1AP）都跑在 SCTP 上。N3 和 F1-U 是使用者面，走 GTP-U／UDP／IP。前傳的 C-plane 雖然也叫 C-plane，但走的是 eCPRI over Ethernet，沒有 SCTP。\n容易卡住的地方：很多人記成「C-plane 就是 SCTP」，於是把前傳 C-plane 也選進去。前傳那段的堆疊是 eCPRI／Ethernet，要看堆疊，不要只看名字裡有沒有 C-plane。"
  },
  {
   "n": 5,
   "type": "multi",
   "q": "CU-CP 與 DU 之間的 SCTP association 已經建立。這代表下列哪些事情？（選出所有正確答案）",
   "o": [
    "兩端的 IP 位址可以互通",
    "兩端之間已經有一條可靠的訊息傳輸通道",
    "使用者資料已經可以開始傳送",
    "F1 Setup 一定會成功",
    "兩端的應用層設定（例如 PLMN、小區資訊）一定相容"
   ],
   "a": [
    0,
    1
   ],
   "e": "SCTP association 建好，代表 IP 可達、傳輸層的可靠通道已經準備好，這是第一步。F1 Setup 是第二步，要交換節點與服務資訊，仍可能因設定不相容被拒絕。使用者資料走 F1-U，跟 F1-C 的 SCTP 無關，還要等承載建好才會有。\n容易卡住的地方：「連上了」聽起來像「好了」。把兩件事分開記：通道通了，不代表對方願意合作。"
  },
  {
   "n": 6,
   "type": "multi",
   "q": "N3 和 F1-U 都使用 GTP-U／UDP／IP。下列哪些是兩者不同的地方？（選出所有正確答案）",
   "o": [
    "隧道的兩個端點",
    "是否用 TEID 識別隧道",
    "GTP-U payload 的內容",
    "UDP 是否提供可靠重傳",
    "GTP-U 擴充標頭的內容"
   ],
   "a": [
    0,
    2,
    4
   ],
   "e": "N3 在 CU-UP 與 UPF 之間，擴充標頭是 PDU Session Container（QFI），payload 是 UE 的 IP 封包；F1-U 在 CU-UP 與 DU 之間，擴充標頭是 NR RAN Container（NR-U），payload 是 PDCP PDU。兩者相同的是基礎堆疊：UDP 都不提供可靠重傳，GTP-U 也都用 TEID 識別隧道。\n容易卡住的地方：「基礎堆疊相同」不等於「同一條隧道」，也不等於「內容相同」。重點在後半：擴充標頭、端點與 payload 都不同。"
  },
  {
   "n": 7,
   "type": "cls",
   "q": "把每個介面放到它所使用的承載方式底下。",
   "items": [
    "F1-U",
    "Open Fronthaul C-plane",
    "N2",
    "E1",
    "N3",
    "Open Fronthaul U-plane",
    "F1-C"
   ],
   "groups": [
    {
     "t": "AP／SCTP／IP",
     "s": [
      {
       "a": 2
      },
      {
       "a": 3
      },
      {
       "a": 6
      }
     ]
    },
    {
     "t": "GTP-U／UDP／IP",
     "s": [
      {
       "a": 4
      },
      {
       "a": 0
      }
     ]
    },
    {
     "t": "eCPRI／Ethernet",
     "s": [
      {
       "a": 1
      },
      {
       "a": 5
      }
     ]
    }
   ],
   "e": "N2、E1、F1-C 是控制面，應用協定（NGAP、E1AP、F1AP）放在 SCTP 上；N3、F1-U 是使用者面，資料由 GTP-U 封裝、放在 UDP 上；前傳的 C-plane 和 U-plane 都是 eCPRI over Ethernet。\n容易卡住的地方：分類的依據是「堆疊」，不是「名字裡有沒有 C 或 U」。前傳 C-plane 名字有 C，卻不在 SCTP 那一類。"
  },
  {
   "n": 8,
   "type": "cls",
   "q": "把每項工作放到負責它的節點。",
   "items": [
    "把 F1AP 的設定轉成自己的排程與處理",
    "接收 AMF 送來的 NGAP 訊息",
    "Low-PHY 與射頻",
    "處理使用者資料的 PDCP",
    "RLC",
    "透過 E1AP 下達承載設定",
    "產生前傳 C-plane 訊息",
    "終止 N3 的 GTP-U 隧道",
    "High-PHY",
    "MAC 排程"
   ],
   "groups": [
    {
     "t": "CU-CP",
     "s": [
      {
       "a": 1
      },
      {
       "a": 5
      }
     ]
    },
    {
     "t": "CU-UP",
     "s": [
      {
       "a": 3
      },
      {
       "a": 7
      }
     ]
    },
    {
     "t": "DU",
     "s": [
      {
       "a": 0
      },
      {
       "a": 4
      },
      {
       "a": 6
      },
      {
       "a": 8
      },
      {
       "a": 9
      }
     ]
    },
    {
     "t": "RU",
     "s": [
      {
       "a": 2
      }
     ]
    }
   ],
   "e": "CU-CP 是控制面的協調者：接 NGAP，再用 E1AP、F1AP 指揮 CU-UP 和 DU。CU-UP 處理使用者資料：終止 N3，做 PDCP。DU 終止 F1AP、做 RLC／MAC／High-PHY，MAC 排程的結果由 DU 產生前傳 C-plane 訊息。RU 只做射頻與 Low-PHY。\n容易卡住的地方：最常放錯的是「產生前傳 C-plane 訊息」，很多人會放到 CU-CP。前傳控制是 DU 根據自己的排程產生的。"
  },
  {
   "n": 9,
   "type": "cls",
   "q": "UE 正在下載檔案。把下行使用者資料從 UPF 到 UE 方向依序經過的介面與處理排好（有兩個項目用不到）。",
   "items": [
    "F1-U（GTP-U）",
    "RU：Low-PHY 與射頻",
    "E1（E1AP）",
    "N3（GTP-U）",
    "DU：RLC、MAC、High-PHY",
    "CU-UP：PDCP 處理",
    "前傳 U-plane（頻域 IQ）",
    "F1-C（F1AP）"
   ],
   "groups": [
    {
     "t": "由 UPF 往 UE 的順序",
     "s": [
      {
       "l": "第 1 站",
       "a": 3
      },
      {
       "l": "第 2 站",
       "a": 5
      },
      {
       "l": "第 3 站",
       "a": 0
      },
      {
       "l": "第 4 站",
       "a": 4
      },
      {
       "l": "第 5 站",
       "a": 6
      },
      {
       "l": "第 6 站",
       "a": 1
      }
     ]
    }
   ],
   "e": "下行資料從 UPF 經 N3 到 CU-UP，CU-UP 做 PDCP 處理後經 F1-U 送到 DU，DU 做 RLC、MAC、High-PHY 後，以頻域 IQ 經前傳 U-plane 送到 RU，RU 完成 Low-PHY 與射頻後從天線送出。E1 和 F1-C 只傳控制訊息，使用者資料不會經過。\n容易卡住的地方：如果把 E1 或 F1-C 排進來，代表還是用「線有連到」來判斷資料路徑。資料路徑要沿著 GTP-U 和前傳 U-plane 走。"
  },
  {
   "n": 10,
   "type": "order",
   "q": "UE 從開機到可以上網，把下列程序排成正確的先後順序。",
   "items": [
    "RRC Setup：建立 UE 與 gNB 之間的 RRC 連線",
    "Registration：UE 透過 NAS 向 AMF 註冊",
    "PDU Session Establishment：向 5GC 要求建立資料會話",
    "使用者資料開始經 N3 在 CU-UP 與 UPF 之間傳送"
   ],
   "e": "UE 要先有 RRC 連線，才有管道和網路講話；註冊用的 NAS 訊息就是經由 RRC 帶上去的。註冊成功只代表網路認得這支 UE，要上網還得建立 PDU Session，網路這時才會設好 N3 的 GTP-U 隧道和無線承載，使用者資料才有路可走。\n容易卡住的地方：Registration 和 PDU Session 很容易被當成同一件事。記成兩步：先「報到」，再「開通資料」。"
  },
  {
   "n": 11,
   "type": "order",
   "q": "DU 開機後要和 CU-CP 建立 F1-C。把下列步驟排成正確的順序。",
   "items": [
    "DU 與 CU-CP 建立 SCTP association",
    "DU 送出 F1 SETUP REQUEST，帶上自己服務的小區資訊",
    "CU-CP 回覆 F1 SETUP RESPONSE，可附上要啟用的小區清單"
   ],
   "e": "F1AP 跑在 SCTP 上，所以傳輸層的 association 要先建好。F1 Setup 由 DU 發起，DU 在 Request 裡告訴 CU-CP 自己服務哪些小區；CU-CP 檢查設定相容後回覆 Response，並可指定要啟用哪些小區。\n容易卡住的地方：很多人以為 F1 Setup 是 CU 主動下發設定。實際上是 DU 先報上自己的能力，CU 再決定接不接受。"
  },
  {
   "n": 12,
   "type": "order",
   "q": "在 N3 上抓到一個下行使用者封包。從 IP 層開始，由外到內排出各層的順序。",
   "items": [
    "外層 IP（CU-UP 與 UPF 的位址）",
    "UDP",
    "GTP-U 標頭（含 TEID，擴充標頭帶 QFI）",
    "內層 IP（UE 與遠端主機的位址）",
    "UE 的 TCP／UDP 與應用資料"
   ],
   "e": "N3 是 GTP-U 隧道：外層 IP 和 UDP 負責把封包送到隧道另一端，GTP-U 標頭用 TEID 指出是哪一條隧道、用 QFI 指出是哪個 QoS Flow，GTP-U 的 payload 才是 UE 原本的 IP 封包。\n容易卡住的地方：同一個封包裡有兩層 IP。外層屬於網路設備，內層屬於使用者，排序時把 GTP-U 當成分界線就不會亂。"
  },
  {
   "n": 13,
   "type": "match",
   "q": "把每個介面對到它使用的應用層協定。",
   "pairs": [
    [
     "N2",
     "NGAP"
    ],
    [
     "E1",
     "E1AP"
    ],
    [
     "F1-C",
     "F1AP"
    ],
    [
     "Xn-C",
     "XnAP"
    ]
   ],
   "e": "控制面介面的應用協定都以介面名稱命名：N2 上是 NGAP（gNB 與 AMF），E1 上是 E1AP（CU-CP 與 CU-UP），F1-C 上是 F1AP（CU-CP 與 DU），Xn-C 上是 XnAP（gNB 與 gNB）。它們都跑在 SCTP 上。\n容易卡住的地方：N2 的協定叫 NGAP，不叫 N2AP。NG 是整個 gNB 與 5GC 之間的參考點名稱，N2 是其中控制面那一條。"
  },
  {
   "n": 14,
   "type": "match",
   "q": "把每個節點對到它主要負責的工作。",
   "pairs": [
    [
     "AMF",
     "UE 的註冊、連線與移動性管理"
    ],
    [
     "UPF",
     "5GC 的使用者面，負責資料轉送與路由"
    ],
    [
     "CU-UP",
     "使用者資料的 PDCP 處理"
    ],
    [
     "DU",
     "RLC、MAC 排程與 High-PHY"
    ],
    [
     "RU",
     "Low-PHY 與射頻"
    ]
   ],
   "e": "AMF 和 UPF 在 5GC，一個管控制、一個管資料。gNB 拆開後，CU-UP 處理使用者資料的 PDCP，DU 做 RLC、MAC 與 High-PHY，RU 只做 Low-PHY 與射頻（O-RAN 7.2x 切分）。\n容易卡住的地方：MAC 排程放在 DU，不在 RU。RU 只照 DU 經前傳 C-plane 給的指示發射，不自己決定資源。"
  },
  {
   "n": 15,
   "type": "match",
   "q": "把每個現象對到最應該先排查的方向。",
   "pairs": [
    [
     "CU 與 DU 之間的 SCTP association 建不起來",
     "IP 路由、防火牆或 SCTP 埠號設定"
    ],
    [
     "SCTP 已連上，但收到 F1 Setup Failure",
     "F1 Setup Failure 的 cause，以及兩端的 PLMN、NR CGI 等設定"
    ],
    [
     "PDU Session 設定成功，CU-UP 有送上行 GTP-U，UPF 卻完全沒收到",
     "N3 的外層 IP 路由或防火牆，例如 UDP 2152 被擋"
    ]
   ],
   "e": "排查時先判斷失敗發生在哪一層：連 SCTP 都建不起來是傳輸層的問題；SCTP 通了但 Setup 被拒，是應用層設定不相容，要看 cause；控制面都成功但資料過不去，問題在使用者面那條 GTP-U／UDP／IP 路徑。\n容易卡住的地方：三個現象都會被說成「連不上」。先問「哪一層失敗」，才知道該查網路還是查設定。"
  }
 ],
 "abbr": [
  {
   "cat": "核心網",
   "abbr": "AMF",
   "full": "Access and Mobility Management Function",
   "alts": [],
   "e": "5GC 的控制面網元，透過 N2（NGAP）和 CU-CP 溝通，負責註冊、連線與移動性管理。"
  },
  {
   "cat": "介面協定",
   "abbr": "GTP-U",
   "full": "GPRS Tunnelling Protocol User Plane",
   "alts": [
    "GPRS Tunneling Protocol User Plane",
    "GPRS Tunnelling Protocol for the User Plane",
    "GPRS Tunneling Protocol for the User Plane"
   ],
   "e": "封裝使用者資料的隧道協定，跑在 UDP 上（目的埠 2152），用 TEID 識別隧道；N3 和 F1-U 都用它，但擴充標頭不同。"
  },
  {
   "cat": "無線協定",
   "abbr": "MAC",
   "full": "Medium Access Control",
   "alts": [
    "Media Access Control"
   ],
   "e": "在 DU 處理的協定層，負責排程與 HARQ；MAC 排程決定 slot、PRB 等資源，結果由 DU 經前傳 C-plane 告訴 RU。"
  }
 ],
 "groups": [
  {
   "name": "C-plane 不等於 SCTP",
   "qs": [
    4,
    7
   ],
   "key": "SCTP 只出現在 NG／F1／E1 這三個控制面；前傳的 C-plane 走 eCPRI over Ethernet，沒有 IP、也沒有 SCTP。分類時看堆疊，不看名字裡有沒有 C。"
  },
  {
   "name": "通道通了 vs 合作成功",
   "qs": [
    3,
    5,
    15
   ],
   "key": "SCTP association 是通道，Setup 是應用層合作。控制面全部成功，也不代表使用者面那條 GTP-U 路徑是通的。"
  }
 ]
}
```
