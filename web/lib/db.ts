// Third-party imports
import postgres from "postgres";

/**
 * A client connected to the configured Postgres application database.
 */
export const sql = postgres(process.env.DATABASE_URL ?? "", {
  types: {
    bigint: postgres.BigInt,
  },
});
