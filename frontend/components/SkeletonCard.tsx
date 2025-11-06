import styles from "./SkeletonCard.module.css";

export default function SkeletonCard() {
  return (
    <div className={styles.card}>
      <div className={`skeleton ${styles.line}`}></div>
      <div className={styles.grid}>
        <div className="skeleton" style={{ height: 16 }}></div>
        <div className="skeleton" style={{ height: 16 }}></div>
        <div className="skeleton" style={{ height: 16 }}></div>
        <div className="skeleton" style={{ height: 16 }}></div>
      </div>
    </div>
  );
}

