# MÔ TẢ NÂNG CẤP ĐỒ THỊ LIÊN KẾT

Đồ thị liên kết dựa trên sự kết hợp giữa cấu trúc dữ liệu văn bản thuần túy và các nguyên lý của lý thuyết đồ thị. Thay vì lưu trữ trong một cơ sở dữ liệu đóng, ứng dụng quét toàn bộ thư mục (vault) để xây dựng một mạng lưới quan hệ theo thời gian thực.

## Cơ chế vận hành

Dưới đây là chi tiết cơ chế vận hành này:

### 1. Dữ liệu đầu vào: Các liên kết Markdown

Bản đồ liên kết không tự nhiên sinh ra; nó được nuôi dưỡng bởi các kết nối mà bạn tạo ra trong các ghi chú:

* **WikiLinks (`[[Tên ghi chú]]`):** Đây là cách phổ biến nhất. Khi bạn tạo một liên kết này, Ứng dụng hiểu rằng có một mũi tên đi từ ghi chú A đến ghi chú B.
* **Tags (`#vídụ`):** Nếu bạn bật tùy chọn hiển thị thẻ, các thẻ sẽ trở thành các "nút" (nodes) trung gian nối các ghi chú có cùng chủ đề lại với nhau.
* **Folders (Thư mục):** Ứng dụng có thể nhóm các ghi chú dựa trên cấu trúc thư mục để bạn thấy được sự phân bổ dữ liệu.

### 2. Bộ đệm siêu dữ liệu (Metadata Cache)

Để bản đồ không bị chậm khi vault của bạn lớn dần, Ứng dụng duy trì một **Metadata Cache**.

* Khi bạn mở ứng dụng, nó sẽ quét nhanh toàn bộ các tệp `.md`.
* Nó lập chỉ mục (index) tất cả các liên kết xuôi (links) và liên kết ngược (backlinks).
* Mỗi tệp được coi là một **Nút (Node)**, và mỗi liên kết là một **Cạnh (Edge)** kết nối hai nút.

### 3. Mô hình đồ thị lực hướng (Force-Directed Graph)

Đây là phần "vật lý" đằng sau cách các nốt di chuyển và sắp xếp trên màn hình. Ứng dụng sử dụng các thuật toán giả lập lực vật lý:

* **Lực đẩy (Repulsion):** Các nút không có liên kết sẽ đẩy nhau ra xa để tránh chồng chéo.
* **Lực hút (Attraction):** Các liên kết đóng vai trò như những "sợi dây thun" kéo các ghi chú có liên quan lại gần nhau.
* **Trọng tâm (Central Force):** Giữ cho toàn bộ bản đồ nằm ở giữa màn hình.

### 4. Các lớp lọc và tùy chỉnh (Filters & Groups)

Bạn có thể điều khiển cách bản đồ hiển thị thông qua bảng điều khiển bên phải:

* **Filters:** Cho phép ẩn/hiện các tệp chưa có liên kết (orphans), tệp đính kèm (hình ảnh, PDF), hoặc lọc theo từ khóa.
* **Groups:** Bạn có thể dùng truy vấn (query) để tô màu cho các nhóm ghi chú. Ví dụ: Tất cả ghi chú có thẻ `#research` sẽ có màu xanh lá.
* **Display:** Điều chỉnh độ dày của liên kết, kích thước nút và độ mạnh của lực hút/đẩy.

### 5. Local Graph (Bản đồ cục bộ)

Khác với Global Graph (toàn cảnh), **Local Graph** chỉ tập trung vào một ghi chú hiện tại và các "hàng xóm" của nó. Bạn có thể điều chỉnh **Depth** (Độ sâu) để xem các liên kết cấp 2, cấp 3... Điều này cực kỳ hữu ích để tìm ra những mối liên hệ gián tiếp mà bạn vô tình quên mất trong quá trình nghiên cứu.

## Minh họa

Ứng tạo **bản đồ liên kết** chủ yếu bằng cách đọc các **liên kết nội bộ** giữa các note trong vault, rồi biến chúng thành một **đồ thị mạng**.

Hiểu đơn giản:

**1. Mỗi note là một nút**
Ví dụ bạn có các note:

* `Marketing`
* `SEO`
* `Shopee`
* `Content`

Mỗi note này sẽ trở thành một **điểm** trên graph.

**2. Mỗi internal link là một cạnh nối**
Khi trong note `Marketing` bạn viết:

```md
[[SEO]]
[[Content]]
```

thì Ứng dụng hiểu rằng note `Marketing` đang liên kết tới `SEO` và `Content`.

Kết quả:

* `Marketing` nối với `SEO`
* `Marketing` nối với `Content`

Đó chính là cơ sở để vẽ graph.

**3. Graph view chỉ trực quan hóa cấu trúc liên kết đó**
Ứng dụng không “hiểu nội dung” theo kiểu AI để tự đoán quan hệ ngữ nghĩa sâu.
Nó chủ yếu dựa vào:

* `[[wikilink]]`
* liên kết markdown nội bộ
* tag
* folder
* metadata nếu bạn dùng để lọc

Nên graph mạnh hay yếu phụ thuộc vào việc bạn **có chủ động liên kết note với nhau hay không**.

Ví dụ:

Note `SEO.md`

```md
SEO dùng để tối ưu khả năng tìm kiếm cho [[Shopee]] và hỗ trợ [[Content Marketing]].
```

Thì graph sẽ hiện:

* `SEO` ↔ `Shopee`
* `SEO` ↔ `Content Marketing`

**4. Local Graph và Global Graph khác nhau**

* **Global Graph**: hiển thị toàn bộ mạng liên kết trong vault
* **Local Graph**: chỉ hiển thị các note liên quan đến note đang mở, thường theo 1–2 cấp liên kết

Nên nếu bạn thấy graph quá rối, thường dùng Local Graph sẽ dễ nhìn hơn.

**5. Backlinks cũng góp phần tạo bản đồ**
Nếu note A link tới note B, thì B cũng được xem là có quan hệ với A qua backlink.
Ví dụ:

* `Marketing` link tới `SEO`
* Trong graph, mối liên hệ giữa hai note vẫn được thể hiện dù bạn đang đứng ở note `SEO`

**6. Tag không phải note, nhưng vẫn có thể được đưa vào graph**
Nếu bạn bật hiển thị tag, thì `#research`, `#idea`, `#todo` cũng có thể xuất hiện như các nút hoặc tiêu chí nhóm lọc.
Tuy nhiên, tag khác với note:

* note tạo liên kết tri thức cụ thể hơn
* tag chủ yếu dùng để phân loại

**7. Vị trí các nút do thuật toán bố trí lực**
Ứng dụng dùng kiểu sắp xếp dạng force-directed:

* nút có nhiều liên kết sẽ thường nằm gần trung tâm
* cụm note liên quan sẽ tự tụ lại
* note ít liên kết thường nằm rìa ngoài

Vì vậy:

* note nào càng được link nhiều → càng dễ thành “hub”
* các chủ đề cùng liên kết qua nhau → tạo thành “cluster”

**8. Vì sao có note nằm lẻ loi một mình**
Do note đó:

* không link tới note nào
* không được note nào link tới
* hoặc bị bộ lọc graph ẩn đi

Đây là lý do nhiều người dùng Ứng dụng hay tạo:

* note trung tâm
* note chỉ mục
* MOC (Map of Content)

để kéo các note rời rạc vào cùng mạng lưới.

**9. Ứng dụng không tự sinh liên kết hoàn hảo nếu bạn không tổ chức**
Graph đẹp không có nghĩa là kiến thức tốt.
Nếu bạn viết nhiều note nhưng không chèn `[[link]]`, graph sẽ rất nghèo nàn.
Ngược lại, nếu bạn thiết kế hệ thống note tốt, graph sẽ phản ánh rõ:

* chủ đề trung tâm
* cụm kiến thức
* lỗ hổng kiến thức
* những note mồ côi

**10. Cách để graph hữu ích hơn**
Muốn bản đồ liên kết của Ứng dụng thật sự có giá trị, bạn nên:

* liên kết note theo khái niệm liên quan
* dùng note tổng hợp cho từng chủ đề lớn
* tránh chỉ dùng folder mà không tạo link
* tạo note khái niệm, note dự án, note nguồn tham khảo riêng
* định kỳ kiểm tra orphan notes

Ví dụ rất dễ hình dung:

`Nghiên cứu định lượng.md`

```md
Liên quan đến [[SEM]], [[EFA]], [[CFA]], [[Bảng hỏi khảo sát]]
```

`SEM.md`

```md
SEM thường được dùng sau [[CFA]] và có liên hệ với [[Mô hình nghiên cứu]]
```

Khi đó graph sẽ hiện ra một cụm phương pháp nghiên cứu khá rõ ràng.
