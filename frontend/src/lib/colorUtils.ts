// 标签颜色调色板（与后端 backend/app/utils/color_generator.py 一致）
const TAG_COLORS = [
  "#EF4444",
  "#F59E0B",
  "#10B981",
  "#3B82F6",
  "#8B5CF6",
  "#EC4899",
  "#6366F1",
  "#14B8A6",
];

/** 随机选择一个调色板颜色 */
export function generateRandomColor(): string {
  const index = Math.floor(Math.random() * TAG_COLORS.length);
  return TAG_COLORS[index];
}
