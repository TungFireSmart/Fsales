# Nghiên cứu trycompai/crm — Bài học nâng cấp Fsales thành AI agent

*(Lưu ý: repo đúng tên là `trycompai/crm`, không phải `trycomai/crm` — dễ gõ nhầm vì tên công ty là Comp AI. Repo mã nguồn mở, MIT licence, ~7.5k sao trên GitHub, ra mắt đầu tháng 8/2026: https://github.com/trycompai/crm, trang giới thiệu https://trycrm.ai)*

## 1. Ý tưởng cốt lõi khác biệt hoàn toàn so với "CRM + chatbot"

Hầu hết CRM "có AI" hiện nay là một CSDL với form nhập liệu, rồi gắn thêm một ô chat bên cạnh để hỏi đáp. trycompai/crm làm ngược lại: **agent không phải là một tính năng của CRM — CRM là nơi agent ghi lại những gì nó tìm ra.** Agent chạy trên một deployment riêng, theo lịch riêng, với một hàng đợi công việc riêng. Nó tự quyết định xem tiếp theo nên nhìn vào đâu, tự đặt lịch follow-up, tiêu một "ngân sách nghiên cứu" mỗi phiên, và dừng lại khi hết ngân sách. Đóng trình duyệt lại, agent vẫn tiếp tục chạy — không phải mô hình request–response.

Đây là điểm mấu chốt cần thấm trước khi bàn kỹ thuật: nếu Fsales chỉ thêm một chatbot trả lời câu hỏi về dữ liệu có sẵn, đó vẫn là "CRM + chatbot". Để thực sự thành "AI agent", Fsales cần một tiến trình nền chủ động tự nghiên cứu, tự điền dữ liệu, tự đặt lịch nhắc việc — con người chỉ xem lại và phê duyệt.

## 2. Nguyên tắc kỹ thuật đáng học — và vì sao mỗi nguyên tắc tồn tại

### a) "Evidence, không phải confidence"

Không có tool nào của agent được phép tự chấm điểm độ tin cậy (confidence score) cho phát hiện của chính nó. Lý do nêu thẳng trong docs: "một model được yêu cầu tự chấm điểm chắc chắn của mình sẽ làm vậy, và nó sẽ sai theo hướng khiến nó trông có ích." Thay vào đó, mỗi tool chỉ báo cáo những gì nó *quan sát được* (ví dụ: "tìm thấy chữ ký email trùng khớp", "tài khoản GitHub xác nhận danh tính") và một hệ thống trung tâm (`lib/evidence.ts`) tự tính điểm dựa trên các bằng chứng đó, theo băng (band): bằng chứng mạnh thì ghi thẳng vào hồ sơ, bằng chứng yếu chỉ tạo đề xuất chờ người duyệt.

**Bài học cho Fsales:** nếu AI agent tự động điền thông tin khách hàng (công ty, chức danh, nhu cầu...), đừng để model tự nói "tôi chắc 85%". Hãy thiết kế nguồn dữ liệu rõ ràng (email, lịch sử liên hệ, tra cứu web) và một quy tắc cứng: nguồn mạnh (ví dụ chữ ký email chính chủ) → ghi thẳng; nguồn yếu (suy đoán từ tên công ty tương tự) → chỉ đề xuất, sale duyệt tay. Một dữ liệu sai mà tự tin là hại hơn một ô trống, vì không ai phát hiện ra nó sai.

### b) Agent tự vận hành qua hàng đợi công việc, không phải cron cứng

Không có lịch "5 phút chạy 1 lần list khách". Thay vào đó mỗi bản ghi (contact/company/deal) có một cột `dueAt` trong bảng công việc; agent tự `claim` các dòng đến hạn bằng khóa hàng (`FOR UPDATE SKIP LOCKED`) để nhiều tiến trình không giẫm lên nhau, và khi agent muốn xem lại ai đó sau, nó phải tự gọi `schedule_recheck` kèm **lý do** — lý do này hiển thị cho nhân viên sale. Nguyên tắc: "một agent không thể nói vì sao 14 ngày nữa nó sẽ quay lại thì không có lý do, nó chỉ có một giá trị mặc định."

**Bài học cho Fsales:** thay vì lịch quét toàn bộ database định kỳ, nên có cơ chế mỗi khách hàng/lead tự mang theo "ngày cần xem lại" + lý do, và agent chỉ xử lý các bản ghi đến hạn. Sale nhìn vào sẽ thấy "vì sao AI sẽ nhắc lại khách này ngày X" thay vì một hộp đen.

### c) Ranh giới rõ ràng: API không được "thông minh"

API (backend) chỉ có nhiệm vụ báo "việc gì đó vừa xảy ra" (có thread mới, có công ty mới được tạo, có người lạ trong cuộc họp...) bằng cách ghi một dòng vào hàng đợi. Toàn bộ "trí tuệ" — tra cứu, làm giàu dữ liệu, chấm điểm, khớp danh tính, quyết định — nằm hoàn toàn trong agent riêng biệt. Lý do được ghi rõ trong docs: từng có hai bộ so khớp danh tính bị copy ở cả API và agent, và chúng trôi dạt (drift) khác nhau dần cho tới khi một bản lỗi tới mức khớp *mọi* công ty trên đời.

**Bài học cho Fsales:** nếu kiến trúc hiện tại của Fsales có logic nghiệp vụ "thông minh" rải rác ở nhiều lớp (backend, frontend, script riêng lẻ), đây là lúc gom lại một chỗ duy nhất. Tách bạch: lớp lõi (ghi nhận sự kiện) và lớp agent (ra quyết định) — tránh trùng lặp logic ở hai nơi rồi lệch pha nhau theo thời gian.

### d) Mỗi nguồn dữ liệu bên ngoài là tùy chọn, agent tự thích nghi

Agent chạy được ngay cả khi không có API key nào — nó vẫn đọc lịch sử liên hệ nội bộ (email, cuộc họp) miễn phí, đó vốn là bằng chứng tốt nhất ("không nhà cung cấp dữ liệu nào bán được một câu trả lời từ chính địa chỉ email của người đó"). Mỗi API key mở thêm một nguồn tra cứu, và agent được thông báo ngay đầu phiên nguồn nào đang bật/tắt, để nó lên kế hoạch phù hợp thay vì gọi thử rồi mới biết là thiếu key.

**Bài học cho Fsales:** thiết kế các "công cụ" nghiên cứu (tra cứu web, LinkedIn, thông tin doanh nghiệp...) là plugin có thể bật/tắt độc lập theo ngân sách/hợp đồng dữ liệu, không phải phụ thuộc cứng. Agent nên biết trước "mình có gì" thay vì dò dẫm.

### e) Sandbox an toàn: không mạng, không quyền truy cập DB

Agent có một sandbox chạy lệnh (bash, đọc file) để làm việc như phân tích, so sánh dữ liệu tháng này với tháng trước — nhưng sandbox đó **không có kết nối mạng ra ngoài** (deny-all egress) và **không bao giờ được cấp `DATABASE_URL`**. Lý do: một shell có cả thông tin đăng nhập DB lẫn quyền truy cập mạng là "hình dạng của một vụ rò rỉ dữ liệu" ngay cả trong công cụ nội bộ.

**Bài học cho Fsales:** nếu để agent chạy code/script tự động (ví dụ để phân tích số liệu), cách ly nghiêm ngặt: không cho sandbox đó cùng lúc vừa có mạng vừa có khóa truy cập dữ liệu khách hàng. Đây là điểm bảo mật rất đáng áp dụng, đặc biệt nếu Fsales xử lý dữ liệu khách hàng nhạy cảm.

### f) Ba nguyên tắc biên giới dữ liệu (data boundaries)

1. Không đưa nguyên văn dữ liệu khách hàng vào truy vấn bên thứ ba — chỉ đưa câu hỏi đã được suy ra (derived).
2. Không đưa nội dung hộp thư vào sandbox — vòng đời khác nhau.
3. Không log bất cứ thứ gì nhạy cảm — đọc không đồng nghĩa với ghi log.

**Bài học cho Fsales:** nếu tích hợp AI của bên thứ ba (OpenAI, Perplexity...) để tra cứu, tuyệt đối không gửi nguyên email/thông tin cá nhân khách hàng ra ngoài — chỉ gửi câu hỏi đã ẩn danh hóa.

### g) Giao diện "trò chuyện với từng bản ghi" thay vì chatbot chung chung

Mỗi khách hàng/công ty/deal có tab **Agent** riêng — xem được từng bước agent đã làm, những manh mối nó bỏ qua và vì sao, trả lời câu hỏi ngay tại chỗ khi nó không phân biệt được hai người trùng tên. Câu hỏi gợi ý cũng khác nhau theo loại bản ghi: với một người thì hỏi "Người này là ai?", với công ty thì "Họ làm gì?", với deal thì "Deal đang ở đâu?". Cuộc trò chuyện được lưu bền, tải lại trang không mất, và có index rõ trong URL để chia sẻ được như một link.

**Bài học cho Fsales:** thay vì một ô chat AI chung ở góc màn hình, nên gắn agent theo từng khách hàng/cơ hội bán hàng cụ thể, với ngữ cảnh (context) được nạp sẵn — sale mở lên là agent đã biết đang nói về ai, không cần hỏi lại.

### h) Không đoán mò danh tính, không tự nhận nhiều tổ chức không cần thiết

`search_crm` cố ý *không* fuzzy-match: tìm "Northwind" ra "Northwind Savings Group" là hữu ích, nhưng "Marchetti" ra "Marchetta" là một bản ghi sai về một con người thật — đây là lỗi tệ nhất mà cả hệ thống được thiết kế để tránh. Đồng thời hệ thống cố tình **không có khái niệm multi-tenant/organization** vì đây là công cụ nội bộ một công ty — giữ nguyên tắc đơn giản: đăng nhập được là thấy hết.

**Bài học cho Fsales:** cân nhắc mức độ multi-tenant cần thiết thực sự (nếu Fsales phục vụ nhiều công ty/chi nhánh khác nhau thì vẫn cần, nhưng đừng thêm lớp phân quyền phức tạp nếu không thực sự cần — mỗi lớp không cần thiết là một chỗ để lỗi ẩn náu).

## 3. Ngăn xếp công nghệ họ dùng (tham khảo, không nhất thiết phải theo)

Turborepo monorepo trên Bun · agent framework "eve" (Vercel) cho phiên làm việc bền vững, tool-as-file, skill-as-markdown, lịch-as-file · Next.js App Router + shadcn/ui cho frontend · NestJS + tRPC cho API (kiểu dữ liệu an toàn từ Prisma đến ô bảng) · Postgres (Neon) + Redis tùy chọn · Better Auth chỉ đăng nhập Google. Điểm đáng chú ý nhất không phải công nghệ cụ thể, mà là **cách chia tách rõ ràng ba deployment độc lập** (agent / app / api) chỉ chia sẻ database — giúp agent có thể chết, redeploy, chạy chậm mà không ảnh hưởng đến app chính.

## 4. Đề xuất lộ trình áp dụng cho Fsales

Vì tôi chưa có thông tin cụ thể về kiến trúc hiện tại của Fsales (thư mục dự án đang trống), đề xuất dưới đây ở mức nguyên tắc — nên điều chỉnh khi có chi tiết hệ thống hiện tại.

**Giai đoạn 1 — nền tảng dữ liệu, chưa cần AI:**
Thêm cơ chế "hàng đợi sự kiện" (một bản ghi mới, một email vào, một cuộc gọi kết thúc → ghi một dòng sự kiện) tách biệt khỏi logic nghiệp vụ hiện tại. Đây là nền để agent sau này "lease" và xử lý, mà không cần đổi kiến trúc lõi ngay.

**Giai đoạn 2 — agent nghiên cứu chạy nền:**
Xây một tiến trình agent riêng (có thể độc lập với backend Fsales hiện tại) đọc hàng đợi sự kiện, tự làm giàu dữ liệu khách hàng/lead bằng các nguồn có sẵn (lịch sử liên hệ nội bộ trước — miễn phí và đáng tin nhất, sau đó mới tới nguồn trả phí như tra cứu doanh nghiệp/LinkedIn). Áp dụng nguyên tắc evidence-based: ghi thẳng khi bằng chứng mạnh, đề xuất chờ duyệt khi bằng chứng yếu.

**Giai đoạn 3 — giao diện trò chuyện theo từng bản ghi:**
Thêm tab "Agent" cho từng khách hàng/deal trong Fsales, hiển thị agent đã làm gì, đang nghĩ gì, và cho phép sale hỏi trực tiếp trong ngữ cảnh bản ghi đó.

**Giai đoạn 4 — agent tự đặt lịch & agent tạo agent:**
Cho phép agent tự đặt lịch nhắc lại (kèm lý do hiển thị cho sale) và tiến xa hơn: cho phép người dùng mô tả một quy trình bằng câu tiếng Việt tự nhiên ("mỗi thứ Hai, làm giàu lại thông tin các khách hàng chưa liên hệ trong 4 tuần") để tạo ra một "agent con" chạy theo lịch riêng.

## 5. Câu hỏi cần làm rõ để lập kế hoạch chi tiết hơn

Để đưa ra kế hoạch sát với thực tế Fsales (không phải nguyên tắc chung chung), sẽ cần biết: kiến trúc hiện tại của Fsales (ngôn ngữ, framework, database), Fsales đang lưu những loại dữ liệu nào (khách hàng, deal, lịch sử liên hệ...), và mức độ tích hợp email/lịch hiện có (đây là nguồn dữ liệu "miễn phí, đáng tin nhất" mà trycompai/crm ưu tiên khai thác trước).

---

**Nguồn:**
- [GitHub - trycompai/crm](https://github.com/trycompai/crm)
- [trycompai/crm README](https://raw.githubusercontent.com/trycompai/crm/main/README.md)
- [docs/agent.md](https://raw.githubusercontent.com/trycompai/crm/main/docs/agent.md)
- [docs/api.md](https://raw.githubusercontent.com/trycompai/crm/main/docs/api.md)
- [Trang giới thiệu sản phẩm — trycrm.ai](https://trycrm.ai/)
