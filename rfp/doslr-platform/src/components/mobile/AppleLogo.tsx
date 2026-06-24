type Props = {
  className?: string;
};

export default function AppleLogo({ className = "h-[72px] w-[72px]" }: Props) {
  return (
    <svg viewBox="0 0 814 1000" className={className} aria-hidden>
      <defs>
        <linearGradient id="appleSilver" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#f5f5f7" />
          <stop offset="45%" stopColor="#d2d2d7" />
          <stop offset="100%" stopColor="#a1a1a6" />
        </linearGradient>
      </defs>
      <path
        fill="url(#appleSilver)"
        d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76.5 0-103.7 40.8-165.9 40.8s-105.6-57-155.5-127C46.7 790.7 0 663 0 541.8c0-194.4 126.4-297.5 250.8-297.5 66.1 0 121.2 43.4 162.7 43.4 38.5 0 98.5-46 176.5-46 28.2 0 129.9 2.6 196.1 99.4zM554.1 159.4c31.1-36.9 53.1-88.1 53.1-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.2 32.4-54.4 83.8-54.4 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.8 1.3 14.4 1.3 45.5 0 103.1-30.4 133.2-71.3z"
      />
    </svg>
  );
}
