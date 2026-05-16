Dưới đây là **hệ quy tắc thực dụng, nhất quán và đã được chuẩn hóa** để khởi tạo 4 loại note trong hệ thống quản lý tri thức có graph view:

* `source_note`
* `concept_note`
* `synthesis_note`
* `board_note`

---

# 1. Nguyên tắc chung của toàn hệ thống

## 1.1. Hệ thống có đúng 4 loại note

Ứng dụng sử dụng **4 loại note** sau:

* `source_note`
* `concept_note`
* `synthesis_note`
* `board_note`

Mỗi loại note có một vai trò riêng và không nên bị dùng lẫn lộn.

---

## 1.2. Mỗi note phải có vai trò rõ ràng

Không nên tạo note mà không biết nó thuộc loại nào.

Mỗi note nên trả lời được một câu hỏi trung tâm:

* `source_note` → “Nguồn này nói gì?”
* `concept_note` → “Khái niệm này là gì?”
* `synthesis_note` → “Nhiều ý này ghép lại cho thấy điều gì?”
* `board_note` → “Toàn bộ bảng phân tích này cho thấy bức tranh chung nào?”

---

## 1.3. Một note không nên ôm quá nhiều chức năng

Ví dụ không nên để một note vừa là:

* tóm tắt tài liệu
* vừa giải thích khái niệm
* vừa viết lập luận tổng hợp
* vừa diễn giải bảng meta-analysis

Làm vậy sau này rất khó link, khó mở rộng, và graph sẽ rối.

---

## 1.4. Ưu tiên liên kết bằng `[[wikilink]]`

Tag dùng để phân loại.
Wikilink dùng để xây mạng tri thức.

Nên ưu tiên:

```md
[[SCCT]]
[[TPB]]
[[Yếu tố cá nhân]]
```

hơn là chỉ dùng:

```md
#scct #tpb #personal-factor
```

---

## 1.5. Mỗi note nên có một trọng tâm

Một note tốt thường chỉ có:

* 1 nguồn chính
* hoặc 1 khái niệm chính
* hoặc 1 câu hỏi tổng hợp chính
* hoặc 1 board phân tích chính

---

## 1.6. Tên note phải phản ánh đúng bản chất

Chỉ nhìn tên note là phải đoán được vai trò của nó.

Ví dụ tốt:

* `Lent et al. (1994)`
* `SCCT`
* `Syns - So sánh SCCT và TPB trong lựa chọn ngành`
* `Board - các nhân tố ảnh hưởng đến chọn ngành`

Ví dụ kém:

* `ghi chú 1`
* `note mới`
* `tài liệu hay`
* `ý tưởng linh tinh`

---

# 2. Quy tắc cho `source_note`

## 2.1. `source_note` là gì

Đây là note dùng để ghi lại nội dung của **một nguồn cụ thể**:

* sách
* bài báo
* báo cáo
* video
* podcast
* website
* file PDF
* tài liệu lớp học

Nó trả lời câu hỏi:
**“Nguồn này nói gì?”**

---

## 2.2. Mục đích

`source_note` dùng để:

* lưu thông tin từ nguồn gốc
* tách biệt cái tác giả nói với cái bạn nghĩ
* làm nguyên liệu cho `concept_note`, `synthesis_note` và `board_note`

Nó là **đầu vào** của hệ thống tri thức.

---

## 2.3. Khi nào tạo `source_note`

Tạo khi:

* bạn đọc một bài báo quan trọng
* bạn học từ một chương sách
* bạn muốn trích dẫn lại đúng nguồn
* bạn cần giữ lại luận điểm, số liệu, định nghĩa từ tác giả

Không nhất thiết nguồn nào cũng phải có `source_note`.
Chỉ nên tạo khi nguồn đó có giá trị tái sử dụng.

---

## 2.4. Nội dung nên có

Một `source_note` tốt nên có:

* thông tin nguồn
* tóm tắt ngắn
* luận điểm chính
* khái niệm quan trọng
* trích dẫn đáng giữ
* nhận xét sơ bộ của bạn
* các link sang note liên quan

---

## 2.5. Cấu trúc gợi ý

```md
# Source - Lent et al. (1994)

## Thông tin nguồn
- Tác giả:
- Năm:
- Loại nguồn:
- Chủ đề:

## Tóm tắt ngắn
Nguồn này bàn về...

## Ý chính
- ...
- ...
- ...

## Khái niệm đáng chú ý
- [[SCCT]]
- [[Career choice]]
- [[Self-efficacy]]

## Trích dẫn / dữ kiện quan trọng
- ...

## Gợi ý sử dụng
- Dùng cho [[board các nhân tố ảnh hưởng đến chọn ngành]]
- Dùng để giải thích [[Yếu tố cá nhân]]

## Ghi chú của tôi
- ...
```

---

## 2.6. Quy tắc viết

Trong `source_note`:

* ưu tiên trung thành với nguồn
* phân biệt rõ ý của tác giả và ý của bạn
* không nên biến nó thành bài luận dài của riêng bạn

---

## 2.7. Quy ước đặt tên

Để thống nhất toàn hệ thống, tên `source_note` nên theo dạng:

* `Tác giả (năm)`

Ví dụ:

* `Lent et al. (1994)` --> nếu có từ 3 tác giả trở lên thì lấy tên của tác giả đầu tiên + `et al.`
* `Ajzen (1991)` --> nếu chỉ có 1 tác giả
* `Ajzen & Puma (1994)` --> nếu có 2 tác giả thì sử dụng ký hiệu `&` để nối tên 2 tác giả

Quy ước này được ưu tiên hơn cách đặt tên chỉ gồm tác giả và năm, vì nó giúp nhận diện loại note ngay trong graph và trong danh sách file.

---

# 3. Quy tắc cho `concept_note`

## 3.1. `concept_note` là gì

Đây là note dành cho **một khái niệm, một ý niệm, một phương pháp, một nguyên lý, một biến, hoặc một đối tượng tri thức riêng biệt**.

Nó trả lời câu hỏi:
**“Khái niệm này là gì?”**

---

## 3.2. Mục đích

`concept_note` dùng để:

* tách khái niệm ra khỏi từng nguồn riêng lẻ
* gom hiểu biết về một khái niệm từ nhiều nguồn
* xây mạng tri thức lâu dài

Đây là “viên gạch” của vault tri thức.

---

## 3.3. Khi nào tạo `concept_note`

Tạo khi:

* một khái niệm xuất hiện lặp đi lặp lại
* bạn sẽ dùng lại nó nhiều lần
* nó có quan hệ với nhiều note khác
* bạn muốn định nghĩa và chuẩn hóa cách hiểu

Ví dụ:

* `SCCT`
* `TPB`
* `EFA`
* `CFA`
* `Yếu tố cá nhân`
* `Cơ hội nghề nghiệp`

---

## 3.4. Nội dung nên có

Một `concept_note` tốt nên có:

* định nghĩa hoặc mô tả khái niệm
* bản chất và thành phần
* cách dùng
* khái niệm gần hoặc liên quan
* nguồn tham chiếu
* liên kết tới `synthesis_note` hoặc `board_note` nơi nó được dùng

---

## 3.5. Cấu trúc gợi ý

```md
# Concept - SCCT

## Định nghĩa
SCCT là...

## Thành phần chính
- ...
- ...
- ...

## Ý nghĩa trong nghiên cứu
Khái niệm này hữu ích khi...

## Liên hệ với các khái niệm khác
- [[TPB]]
- [[Self-efficacy]]
- [[Career choice]]

## Nguồn liên quan
- [[Lent et al. (1994)]]

## Board liên quan
- [[Board - Lý thuyết sử dụng trong nghiên cứu chọn ngành]]

## Ghi chú của tôi
- ...
```

---

## 3.6. Quy tắc viết

`concept_note` nên:

* cô đọng
* rõ ràng
* tập trung vào 1 khái niệm
* không viết lan man thành bài luận quá dài

Nếu note quá dài, thường là dấu hiệu bạn đang chuyển sang `synthesis_note`.

---

## 3.7. Quy ước đặt tên

Tên tốt nhất cho `concept_note` là **tên khái niệm trực tiếp**.

Ví dụ:

* `SCCT`
* `TPB`
* `EFA`
* `Supply Chain Resilience`
* `Yếu tố cá nhân`

Không dùng prefix cho `concept_note`, để liên kết trong bài viết và graph được gọn, tự nhiên, và dễ đọc.

---

# 4. Quy tắc cho `synthesis_note`

## 4.1. `synthesis_note` là gì

Đây là note dùng để **ghép, đối chiếu, tổng hợp, diễn giải và rút ra kết luận** từ nhiều note hoặc nhiều nguồn.

Nó trả lời câu hỏi:
**“Khi đặt nhiều ý này lại với nhau, ta hiểu ra điều gì?”**

---

## 4.2. Mục đích

`synthesis_note` dùng để:

* kết nối nhiều `concept_note`
* sử dụng nhiều `source_note` làm bằng chứng
* có thể dựa trên hoặc dẫn chiếu tới `board_note`
* chuyển từ ghi nhớ sang tư duy
* chuẩn bị cho viết luận văn, báo cáo, bài viết, quyết định nghiên cứu

Đây là nơi thể hiện **giá trị tư duy của bạn**.

---

## 4.3. Khi nào tạo `synthesis_note`

Tạo khi:

* bạn có từ 2 nguồn hoặc 2 concept trở lên cần đặt cạnh nhau
* bạn muốn trả lời một câu hỏi lớn hơn một khái niệm đơn lẻ
* bạn cần viết lập luận hoặc mô hình giải thích

Ví dụ:

* `So sánh SCCT và TPB trong nghiên cứu chọn ngành`
* `Vì sao yếu tố cá nhân là trung tâm của mô hình`
* `Tổng hợp các nhân tố ảnh hưởng đến khẳng định chọn ngành`

---

## 4.4. Nội dung nên có

Một `synthesis_note` tốt nên có:

* câu hỏi hoặc vấn đề trung tâm
* các note liên quan
* điểm giống và khác
* mối quan hệ logic
* nhận định riêng
* kết luận hoặc hướng sử dụng

---

## 4.5. Cấu trúc gợi ý

```md
# Synthesis - So sánh SCCT và TPB trong nghiên cứu chọn ngành

## Câu hỏi trung tâm
SCCT và TPB giải thích quyết định chọn ngành khác nhau như thế nào?

## Các note liên quan
- [[SCCT]]
- [[TPB]]
- [[Yếu tố cá nhân]]
- [[Gia đình và người xung quanh]]
- [[board lý thuyết sử dụng trong nghiên cứu chọn ngành]]

## Điểm giống
- ...
- ...

## Điểm khác
- ...
- ...

## Hàm ý cho đề tài của tôi
- ...
- ...

## Kết luận tạm thời
- ...
```

---

## 4.6. Quy tắc viết

Trong `synthesis_note`, bạn nên:

* chủ động viết bằng ngôn ngữ của mình
* chỉ ra quan hệ giữa các ý
* tránh chỉ liệt kê lại ghi chú từ nguồn
* ưu tiên câu trả lời, nhận định, kết luận

Nếu `source_note` là “tác giả nói gì”
và `concept_note` là “khái niệm là gì”
thì `synthesis_note` là:
**“Tôi hiểu gì từ toàn bộ những thứ này?”**

---

## 4.7. Quy ước đặt tên

Để thống nhất toàn hệ thống, tên `synthesis_note` nên theo dạng:

* ký hiệu `~` ở đầu
* một **câu hỏi**
* một **vấn đề**
* hoặc một **kết luận ngắn**

Ví dụ:

* `~ So sánh SCCT và TPB trong nghiên cứu chọn ngành`
* `~ Vì sao yếu tố cá nhân là trung tâm`
* `~ Các nhân tố ảnh hưởng đến quyết định chọn ngành`
* `~ Tại sao SEM phù hợp với mô hình này`

---

# 5. Quy tắc cho `board_note`

## 5.1. `board_note` là gì

`board_note` là note dùng để **rút ra bức tranh tổng thể, mô hình hóa, phân loại, hoặc kết luận bậc cao** từ một **bảng phân tích chung**.

Bảng này có thể là:

* bảng meta-analysis
* bảng tổng hợp tài liệu
* bảng so sánh nghiên cứu
* bảng mã hóa nhân tố
* bảng đối chiếu lý thuyết
* bảng mapping khái niệm
* bảng ma trận nguồn x biến x kết quả

`board_note` trả lời câu hỏi:

**“Khi nhìn toàn bộ bảng phân tích này như một hệ thống, ta rút ra được điều gì?”**

Đây là định nghĩa chính thức của `board_note` trong hệ thống này.
Nó **không** phải note quản lý công việc và **không** thay thế chức năng task/project management.

---

## 5.2. `board_note` khác gì với `synthesis_note`

### 5.2.1. `synthesis_note`

Tổng hợp từ:

* nhiều note
* nhiều concept
* nhiều source
* một câu hỏi hay một chủ đề

Trọng tâm là:

* kết nối ý
* giải thích
* so sánh
* lập luận

Nó trả lời:
**“Nhiều ý này ghép lại cho thấy điều gì?”**

---

### 5.2.2. `board_note`

Tổng hợp từ:

* một bảng phân tích chung đã được cấu trúc hóa
* dữ liệu phân loại, mã hóa, đối chiếu, gom nhóm

Trọng tâm là:

* nhìn toàn cục
* phát hiện mẫu hình
* phân bố xu hướng
* cấu trúc hệ thống
* khoảng trống nghiên cứu
* logic hình thành khung phân tích

Nó trả lời:
**“Toàn bộ bảng phân tích này cho thấy bức tranh chung nào?”**

---

### 5.2.3. Cách nhớ nhanh

* `synthesis_note` = tổng hợp theo **vấn đề**
* `board_note` = tổng hợp theo **bảng phân tích hệ thống**

---

## 5.3. Vai trò của `board_note` trong hệ thống

`board_note` dùng để diễn giải **toàn bộ một bảng phân tích chung** nhằm rút ra:

* cấu trúc chung
* các nhóm chính
* quy luật nổi bật
* dòng nghiên cứu chủ đạo
* khoảng trống
* logic xây dựng mô hình hoặc khung nghiên cứu

Nó là node tổng hợp cấp cao trong graph, có chức năng điều hướng tri thức ở mức toàn cục.

---

## 5.4. Khi nào nên tạo `board_note`

Nên tạo `board_note` khi có ít nhất một trong các trường hợp sau:

* đã có một bảng tổng hợp tài liệu khá lớn và muốn biến nó thành tri thức cấp cao hơn
* không chỉ muốn lưu bảng, mà muốn có một note diễn giải bảng đó nói lên điều gì
* cần một note trung tâm để viết chương tổng quan, lịch sử nghiên cứu, khoảng trống nghiên cứu hoặc khung mô hình
* muốn chuyển từ “bảng dữ liệu tổng hợp” sang “kết luận học thuật có thể viết thành văn”

---

## 5.5. Khi nào không nên tạo `board_note`

Không nên tạo `board_note` nếu:

* mới chỉ có vài note rời rạc, chưa có bảng phân tích đủ rõ
* chỉ đang tóm tắt một nguồn duy nhất
* chỉ đang giải thích một khái niệm
* chỉ đang tổng hợp một câu hỏi nhỏ từ vài note mà chưa dựa trên bảng phân tích hệ thống

---

## 5.6. Nội dung cốt lõi của một `board_note`

Một `board_note` tốt nên có 6 lớp nội dung sau.

### 5.6.1. Xác định bảng nền

Phải nói rõ board này được xây trên bảng nào:

* tên bảng
* phạm vi
* tiêu chí chọn nguồn
* đơn vị phân tích

### 5.6.2. Mô tả cấu trúc bảng

Ví dụ:

* cột tác giả
* năm
* bối cảnh
* biến độc lập
* biến phụ thuộc
* lý thuyết
* phương pháp
* kết quả chính

### 5.6.3. Rút ra mẫu hình

Ví dụ:

* nhân tố nào xuất hiện nhiều nhất
* hướng tác động nào lặp lại
* lý thuyết nào được dùng nhiều
* quốc gia nào được nghiên cứu nhiều
* phương pháp nào chiếm ưu thế

### 5.6.4. Phân loại hoặc nhóm hóa

Ví dụ:

* nhóm nhân tố cá nhân
* nhóm nhân tố xã hội
* nhóm nhân tố thể chế
* nhóm nhân tố truyền thông

### 5.6.5. Chỉ ra khoảng trống hoặc chỗ lệch

Ví dụ:

* thiếu nghiên cứu ở Việt Nam
* ít nghiên cứu về biến phụ thuộc Y
* thiếu tích hợp giữa hai lý thuyết
* còn lệch về mẫu khảo sát hoặc phương pháp

### 5.6.6. Hàm ý cho hệ note hoặc nghiên cứu của bạn

Ví dụ:

* concept nào cần tạo thêm
* synthesis nào cần viết tiếp
* mô hình nào nên chọn
* giả thuyết nào có cơ sở mạnh

---

## 5.7. Cấu trúc chuẩn cho `board_note`

```md
# Board - Các nhân tố ảnh hưởng đến chọn ngành

## Mục đích của board
Board này được xây dựng để...

## Bảng nền / nguồn dữ liệu phân tích
- Tên bảng:
- Phạm vi:
- Số lượng nguồn:
- Tiêu chí chọn:
- Đơn vị phân tích:

## Cấu trúc phân tích của bảng
Bảng gồm các chiều phân tích chính như...

## Các mẫu hình nổi bật
### Mẫu hình 1
...

### Mẫu hình 2
...

### Mẫu hình 3
...

## Các nhóm/chùm nội dung chính
### Nhóm 1
...

### Nhóm 2
...

### Nhóm 3
...

## Khoảng trống / điểm còn thiếu
- ...
- ...
- ...

## Hàm ý đối với hệ thống note
### Concept notes liên quan
- [[...]]
- [[...]]

### Synthesis notes liên quan
- [[...]]
- [[...]]

### Source notes nền
- [[ ...]]
- [[ ...]]

## Hàm ý đối với nghiên cứu
- ...
- ...
- ...

## Kết luận tạm thời
...
```

---

## 5.8. Quy tắc viết `board_note`

### 5.8.1. Không chép lại toàn bộ bảng

`board_note` không phải bản sao của bảng.
Nó là **note diễn giải từ bảng**.

Bảng có thể nằm:

* trong file khác
* trong note riêng
* trong attachment
* trong phần phụ lục

Còn `board_note` chỉ nên viết:

* điều đáng chú ý
* cấu trúc
* xu hướng
* hàm ý

---

### 5.8.2. Luôn viết ở cấp “mẫu hình”

Tránh liệt kê kiểu:

* bài A nói...
* bài B nói...
* bài C nói...

Cách đó giống `source_note` hoặc tổng hợp thô.

`board_note` nên viết ở mức:

* đa số nghiên cứu cho thấy...
* nhóm nghiên cứu này có xu hướng...
* bảng cho thấy ba cụm yếu tố chính...
* phần lớn nguồn tập trung vào...

---

### 5.8.3. Ưu tiên ngôn ngữ phân loại và cấu trúc

Các động từ phù hợp trong `board_note` là:

* cho thấy
* phản ánh
* phân thành
* nổi lên
* lặp lại
* tập trung vào
* nghiêng về
* thiếu vắng
* gợi ý
* xác lập

---

### 5.8.4. Không biến `board_note` thành `synthesis_note` thuần túy

Nếu note chỉ toàn lập luận theo một câu hỏi mà gần như không dựa trên cấu trúc bảng, thì đó không còn là `board_note`.

`board_note` phải giữ được dấu vết rõ ràng của:

* bảng nền
* logic phân tích hệ thống
* diễn giải từ toàn cục

---

### 5.8.5. Kết luận phải ở cấp hệ thống

Kết luận của `board_note` nên trả lời các câu hỏi như:

* toàn cảnh đang trông như thế nào
* mẫu hình nào chiếm ưu thế
* khu vực nào còn trống
* logic chung nào đang hình thành
* điều này dẫn tới bước nghiên cứu tiếp theo nào

---

## 5.9. Quy ước đặt tên

Để thống nhất toàn hệ thống, tên `board_note` nên theo dạng:

* `Board - Chủ đề phân tích`

Ví dụ:

* `Board - Các nhân tố ảnh hưởng đến chọn ngành`
* `Board - Lý thuyết sử dụng trong nghiên cứu chọn ngành`
* `Board - Khoảng trống nghiên cứu chọn ngành`
* `Board - Meta-analysis về lựa chọn ngành`

---

## 5.10. Các kiểu `board_note` phổ biến

Bạn có thể chia `board_note` thành các dạng sau.

### 5.10.1. Literature board

Tổng hợp từ bảng tài liệu nghiên cứu, dùng để rút ra:

* xu hướng nghiên cứu
* nhóm chủ đề
* khoảng trống
* bối cảnh nghiên cứu

### 5.10.2. Theory board

Tổng hợp từ bảng đối chiếu lý thuyết, dùng để rút ra:

* lý thuyết nào giải thích tốt vấn đề nào
* điểm giao nhau giữa các lý thuyết
* logic tích hợp lý thuyết

### 5.10.3. Factor board

Tổng hợp từ bảng mã hóa các nhân tố, dùng để rút ra:

* các nhóm nhân tố chính
* tần suất xuất hiện
* logic gom nhóm
* căn cứ hình thành biến nghiên cứu

### 5.10.4. Method board

Tổng hợp từ bảng phương pháp, dùng để rút ra:

* phương pháp nào được dùng nhiều
* mẫu nghiên cứu nào phổ biến
* hạn chế phương pháp hiện có

### 5.10.5. Gap board

Tổng hợp để xác lập khoảng trống nghiên cứu, dùng để rút ra:

* chỗ nào được nghiên cứu nhiều
* chỗ nào bị bỏ trống
* cơ sở chính đáng cho đề tài của bạn

---

## 5.11. Quan hệ của `board_note` với các note khác

### `board_note` nên link tới `source_note`

Vì bảng nền cuối cùng vẫn xuất phát từ nguồn.

### `board_note` nên link tới `concept_note`

Vì các cột hoặc nhóm phân tích thường quy về khái niệm.

### `board_note` nên link tới `synthesis_note`

Vì từ board sẽ nảy sinh nhiều synthesis cụ thể hơn.

### `synthesis_note` có thể link ngược về `board_note`

Để chỉ ra rằng synthesis này được rút từ một nền phân tích lớn hơn.

`board_note` không phải note “quản lý chung”, mà là node tổng hợp hệ thống trong graph.

---

# 6. Luồng liên kết chuẩn giữa 4 loại note

## 6.1. Luồng chuẩn chính thức

Luồng làm việc chuẩn của hệ thống là:

`source_note`
→ rút ra `concept_note`
→ lập **bảng phân tích chung**
→ viết `board_note`
→ tách ra hoặc phát triển thành `synthesis_note`

Đây là luồng chuẩn chính thức và được ưu tiên khi thiết kế ứng dụng.

---

## 6.2. Giải thích ngắn

Nói đơn giản:

* đọc nguồn
* tách khái niệm
* đưa dữ liệu vào bảng tổng hợp
* diễn giải bức tranh toàn cục thành `board_note`
* từ `board_note` và các `concept_note`, phát triển các `synthesis_note` chuyên đề

---

## 6.3. Quan hệ nên có

### `source_note` nên link tới:

* `concept_note`
* đôi khi tới `board_note`

### `concept_note` nên link tới:

* `source_note`
* `concept_note` khác
* `board_note`
* `synthesis_note`

### `board_note` nên link tới:

* nhiều `source_note`
* nhiều `concept_note`
* các `synthesis_note` được rút ra từ board

### `synthesis_note` nên link tới:

* nhiều `concept_note`
* nhiều `source_note`
* `board_note` liên quan nếu synthesis được phát triển từ board

---

# 7. Quy tắc dùng tag cho 4 loại note

Bạn có thể dùng tag để đánh dấu loại note:

* `#source`
* `#concept`
* `#synthesis`
* `#board`

Tuy nhiên, **tag chỉ là lớp quản lý phụ**.
Cấu trúc thật sự vẫn nên dựa vào:

* tên note
* link giữa các note
* folder nếu cần

---

# 8. Bộ quy tắc ra quyết định nhanh

Khi bạn định tạo note mới, hãy tự hỏi:

## 8.1. Nếu note này chủ yếu ghi từ một tài liệu

→ tạo `source_note`

## 8.2. Nếu note này nhằm giải thích một khái niệm

→ tạo `concept_note`

## 8.3. Nếu note này đang so sánh, đối chiếu, tổng hợp nhiều ý theo một câu hỏi

→ tạo `synthesis_note`

## 8.4. Nếu note này dựa trên một bảng phân tích chung và nhằm rút ra bức tranh toàn cục

→ tạo `board_note`

---

# 9. Bộ quy tắc chống lẫn lộn

## Không nên:

* dùng `board_note` để viết giải thích khái niệm dài
* dùng `source_note` để viết kết luận học thuật của riêng bạn quá nhiều
* dùng `concept_note` để chứa 10 khái niệm khác nhau
* dùng `synthesis_note` như thùng rác gom ý vụn
* dùng `board_note` như nơi quản lý task, checklist, hay tiến độ dự án

---

# 10. Bộ nguyên tắc tối giản nhất

Nếu bạn muốn nhớ cực nhanh, chỉ cần nhớ:

## `source_note`

Ghi lại **nguồn nói gì**

## `concept_note`

Làm rõ **khái niệm là gì**

## `board_note`

Diễn giải **toàn bộ bảng phân tích cho thấy bức tranh chung nào**

## `synthesis_note`

Rút ra **nhiều ý ghép lại cho thấy điều gì**

---

# 11. Mẫu quy ước khuyến nghị cho ứng dụng

## 11.1. Tên thư mục

* `01 Sources`
* `02 Concepts`
* `03 Boards`
* `04 Syntheses`
* `99 Inbox`

---

## 11.2. Tên note

* Source: `source Tác giả năm`
* Concept: `Tên khái niệm`
* Board: `board Chủ đề phân tích`
* Synthesis: `Câu hỏi hoặc kết luận`

---

## 11.3. Tag loại note

* `#source`
* `#concept`
* `#board`
* `#synthesis`

---

## 11.4. Luồng làm việc

* đọc nguồn
* tạo `source_note`
* tách `concept_note`
* lập bảng phân tích chung
* viết `board_note` từ bảng
* phát triển các `synthesis_note` chuyên đề

---

# 12. Kết luận

Hệ thống 4 loại note này được thiết kế để hỗ trợ đồng thời:

* ghi chú nguồn
* chuẩn hóa khái niệm
* tổng hợp theo vấn đề
* tổng hợp theo bảng phân tích hệ thống
* và trực quan hóa graph rõ ràng hơn

Trong graph view:

* `source_note` là node bằng chứng
* `concept_note` là node tri thức chuẩn hóa
* `board_note` là node tổng hợp hệ thống
* `synthesis_note` là node lập luận theo vấn đề

Nếu được giữ đúng vai trò và liên kết đúng luồng, 4 loại note này sẽ tạo ra một graph dễ đọc, có chiều sâu tri thức, và phù hợp cho cả nghiên cứu học thuật lẫn ứng dụng quản lý kiến thức cá nhân.
