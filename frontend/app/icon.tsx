import { ImageResponse } from "next/og";

export const size = {
  width: 64,
  height: 64
};

export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "center",
          background: "#102A43",
          borderRadius: 18,
          display: "flex",
          height: "100%",
          justifyContent: "center",
          position: "relative",
          width: "100%"
        }}
      >
        <div
          style={{
            color: "#14B8A6",
            display: "flex",
            fontSize: 32,
            fontWeight: 700,
            left: 16,
            lineHeight: 1,
            position: "absolute",
            top: 17
          }}
        >
          A
        </div>
        <div
          style={{
            color: "#FDBA74",
            display: "flex",
            fontSize: 28,
            fontWeight: 700,
            position: "absolute",
            right: 14,
            top: 18
          }}
        >
          /
        </div>
      </div>
    ),
    size
  );
}
