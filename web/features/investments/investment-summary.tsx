import { Investment } from "./interfaces";

export class InvestmentSummaryBuilder {
  private readonly _inv: Investment;

  constructor(investment: Investment) {
    this._inv = investment;
  }

  get investorLocation() {
    if (this._inv.investor_country_name && this._inv.investor_region_name) {
      return `(${this._inv.investor_region_name}, ${this._inv.investor_country_name})`;
    } else if (this._inv.investor_country_name) {
      return `(${this._inv.investor_country_name})`;
    } else {
      return "";
    }
  }

  get issuerLocation() {
    if (this._inv.issuer_country_name) {
      return `(${this._inv.issuer_country_name})`;
    } else {
      return "";
    }
  }

  get financialAction() {
    return this._inv.stock_number_of_shares ? "purchased" : "invested";
  }

  get financialAmount() {
    return this._inv.stock_number_of_shares
      ? `${this._inv.stock_number_of_shares.toLocaleString()}`
      : "";
  }

  get financialAmountUnit() {
    return this._inv.stock_number_of_shares ? "shares in" : "";
  }

  get marketValuePrefix() {
    if (this._inv.security_market_value_amount_usd) {
      return `with a total market value of`;
    }
    return "";
  }

  get marketValueAsterisk() {
    return this._inv.security_market_value_conversion_rate == 0 ||
      this._inv.security_market_value_conversion_rate == 1
      ? ""
      : "*";
  }

  get marketValue() {
    return this._inv.security_market_value_amount_usd
      ? `$${this._inv.security_market_value_amount_usd.toLocaleString()} USD${this.marketValueAsterisk}`
      : "";
  }

  get issuerSector() {
    return this._inv.issuer_sector
      ? `, a company within the ${this._inv.issuer_sector} sector`
      : "";
  }

  get originalAmount() {
    return this._inv.security_market_value_amount &&
      this._inv.security_market_value_currency_code &&
      this._inv.security_market_value_currency_code !== "USD"
      ? `${this._inv.security_market_value_amount.toLocaleString()} ${this._inv.security_market_value_currency_code}`
      : "";
  }

  get investmentAuthority() {
    const statements = [];
    if (this._inv.stock_voting_auth_sole) {
      statements.push(
        `${this._inv.stock_voting_auth_sole.toLocaleString()} had sole voting authority rights`,
      );
    }
    if (this._inv.stock_voting_auth_shared) {
      statements.push(
        `${this._inv.stock_voting_auth_shared.toLocaleString()} had shared voting authority rights`,
      );
    }
    if (this._inv.stock_voting_auth_none) {
      statements.push(
        `${this._inv.stock_voting_auth_none.toLocaleString()} had no voting authority rights`,
      );
    }
    if (statements.length == 1) {
      return `Of the shares, ${statements[0]}.`;
    } else if (statements.length == 2) {
      return `Of the shares, ${statements[0]} while ${statements[1]}.`;
    } else if (statements.length == 3) {
      return `Of the shares, ${statements[0]}, ${statements[1]}, and ${statements[2]}.`;
    } else {
      return "";
    }
  }

  get summary() {
    const phrases = [
      this._inv.investor_name,
      this.investorLocation,
      "purchased",
      this.financialAmount,
      "shares",
      this.marketValuePrefix,
      this.marketValue,
      "in",
      this._inv.issuer_name,
      this.issuerLocation,
      this.issuerSector,
      ".",
      this.investmentAuthority,
      this.stockPercentage,
    ];
    return phrases
      .filter((phrase) => phrase !== "")
      .join(" ")
      .replace(/\s+\./, ".")
      .replace(/\s+,/, ",");
  }

  get stockPercentage() {
    if (
      this._inv.stock_percent_ownership &&
      this._inv.stock_percent_voting_power
    ) {
      return `The investor's shares give it ${this._inv.stock_percent_ownership * 1}% ownership and ${this._inv.stock_percent_voting_power * 1}% voting power.`;
    } else if (this._inv.stock_percent_ownership) {
      return `The investor's shares give it ${this._inv.stock_percent_ownership * 1}% ownership.`;
    } else if (this._inv.stock_percent_voting_power) {
      return `The investor's shares give it ${this._inv.stock_percent_voting_power * 1}% voting power`;
    } else {
      return "";
    }
  }
}
