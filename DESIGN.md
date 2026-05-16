---
version: alpha
name: Research PKM Desktop
description: He thong giao dien desktop local-first cho quy trinh nghien cuu PDF va ghi chu Markdown.
colors:
  primary: "#3A5CE6"
  primary-hover: "#2F4CC8"
  secondary: "#5A6076"
  tertiary: "#20A39E"
  neutral: "#F5F5F5"
  surface: "#FFFFFF"
  on-surface: "#1A1A2E"
  border: "#D0D4E8"
  warning: "#8A4B00"
  success: "#166534"
  info: "#1E40AF"
typography:
  headline-md:
    fontFamily: Segoe UI
    fontSize: 18px
    fontWeight: 700
    lineHeight: 1.2
  body-md:
    fontFamily: Segoe UI
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  label-sm:
    fontFamily: Segoe UI
    fontSize: 11px
    fontWeight: 600
    lineHeight: 1.3
rounded:
  sm: 4px
  md: 6px
  lg: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 8px
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  tab-selected:
    backgroundColor: "{colors.primary-hover}"
    textColor: "#FFFFFF"
  badge-info:
    backgroundColor: "#DBEAFE"
    textColor: "{colors.info}"
  badge-success:
    backgroundColor: "#DCFCE7"
    textColor: "{colors.success}"
  app-shell:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-surface}"
  surface-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
  border-subtle:
    backgroundColor: "{colors.border}"
  text-secondary:
    textColor: "{colors.secondary}"
  badge-tertiary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-surface}"
  warning-banner:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.surface}"
---

## Overview

Giao dien huong den toc do thao tac cho nghien cuu hoc thuat: ro rang, tap trung vao noi dung, it nhieu va de quet thong tin. Uu tien tinh on dinh khi lam viec dai gio, tranh cac hieu ung gay mat tap trung.

## Colors

Bang mau su dung nen sang trung tinh, text toi de doc dai, va mot mau primary duy nhat cho hanh dong chinh.

- Primary (#3A5CE6): hanh dong chinh va trang thai dang chon.
- Secondary (#5A6076): thong tin phu, nhan metadata.
- Tertiary (#20A39E): nhan dien phan bo sung (khong dung cho CTA chinh).
- Neutral (#F5F5F5): nen ung dung.
- Surface (#FFFFFF): nen panel, card, input.

## Typography

He thong chu uu tien tinh de doc va mat do thong tin cao tren desktop.

- Headline-md: tieu de man hinh.
- Body-md: noi dung va nhan thong thuong.
- Label-sm: metadata, helper text, badge.

## Layout

Su dung nhip 8px, bo cuc split-pane cho workspace, va margin nhat quan theo view.

- Man hinh chinh: sidebar + content stack + status strip.
- View nghiep vu: margin 16-24px, spacing 8-16px.
- Thanh cong cu va header giu chieu cao nho de uu tien khong gian noi dung.

## Elevation & Depth

Uu tien border va contrast thay cho bong do nang. Panel duoc tach lop bang border nhe va su khac biet giua neutral/surface.

## Shapes

Shape language nhat quan voi bo goc nho, ky luat 4/6/8px. Khong tron lan radius lon va radius vuong trong cung mot view.

## Components

- Buttons: `button-primary` chi danh cho hanh dong quan trong nhat tren moi man hinh.
- Inputs: vien nhe, focus theo primary.
- Tabs: tab dang chon co nen dam va text trang, dam bao contrast.
- Badges: Global/Project mode dung cap mau info/success de nhan dien nhanh.

## Do's and Don'ts

- Do dung primary cho mot CTA quan trong nhat tren tung man hinh.
- Do duy tri contrast toi thieu WCAG AA (4.5:1) cho text thuong.
- Do giu toi da hai muc font weight tren mot view thong thuong.
- Don't dat style inline phan tan khi da co rule trong stylesheet trung tam.
- Don't dung nhieu mau nhan qua giong nhau cho cac hanh dong canh tranh.
