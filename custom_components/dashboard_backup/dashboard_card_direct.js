import { LitElement, html, css } from "https://unpkg.com/lit-element@2.5.1/lit-element.js?module";

class DashboardBackupCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object }
    };
  }

  static get styles() {
    return css`
      .card-content {
        padding: 16px;
      }
      .card-actions {
        display: flex;
        justify-content: space-around;
        padding: 8px;
      }
    `;
  }

  constructor() {
    super();
    this.config = {};
    console.log("Dashboard Backup Card (Direct Import): Constructor called");
  }

  setConfig(config) {
    if (!config.title) {
      config.title = 'Dashboard Backup';
    }
    this.config = config;
    console.log("Dashboard Backup Card (Direct Import): Config set", this.config);
  }

  render() {
    if (!this.config) return html``;

    return html`
      <ha-card header="${this.config.title}">
        <div class="card-content">
          <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <img src="/local/dashboard_backup/dashboard_backup.png" alt="Dashboard Backup" style="width: 40px; height: 40px; margin-right: 16px;">
            <p>${this.config.description || 'Backup and restore your dashboard configuration.'}</p>
          </div>
        </div>
        <div class="card-actions">
          <mwc-button @click="${this._createBackup}">
            <ha-icon icon="mdi:content-save"></ha-icon>
            Backup Dashboard
          </mwc-button>
          <mwc-button @click="${this._restoreBackup}">
            <ha-icon icon="mdi:backup-restore"></ha-icon>
            Restore Dashboard
          </mwc-button>
        </div>
      </ha-card>
    `;
  }

  _createBackup(e) {
    const dashboardId = this.config.dashboard_id || 'lovelace';
    this._hass.callService('dashboard_backup', 'create_backup', {
      dashboard_id: dashboardId
    });
    this._showToast('Creating dashboard backup...');
  }

  _restoreBackup(e) {
    const dashboardId = this.config.dashboard_id || 'lovelace';
    this._hass.callService('dashboard_backup', 'restore_backup', {
      dashboard_id: dashboardId
    });
    this._showToast('Restoring dashboard from backup...');
  }

  _showToast(message) {
    if (this.hass) {
      const event = new CustomEvent('hass-notification', {
        detail: { message },
        bubbles: true,
        composed: true
      });
      this.dispatchEvent(event);
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (this.shadowRoot) {
      this.requestUpdate();
    }
  }

  getCardSize() {
    return 3;
  }
}

// Define the element with error handling
try {
  if (!customElements.get('dashboard-backup-card')) {
    console.log("Dashboard Backup Card (Direct Import): Defining custom element 'dashboard-backup-card'");
    customElements.define('dashboard-backup-card', DashboardBackupCard);
    
    // Add card to custom cards
    window.customCards = window.customCards || [];
    window.customCards.push({
      type: 'dashboard-backup-card',
      name: 'Dashboard Backup Card',
      description: 'A card that provides buttons to backup and restore your dashboard configuration.',
      preview: false
    });
    
    console.info(
      '%c DASHBOARD-BACKUP-CARD (DIRECT IMPORT) %c Version 1.0.0 ',
      'color: white; background: #3498db; font-weight: 700;',
      'color: #3498db; background: white; font-weight: 700;'
    );
  } else {
    console.log("Dashboard Backup Card (Direct Import): Custom element 'dashboard-backup-card' already defined");
  }
} catch (error) {
  console.error("Dashboard Backup Card (Direct Import): Error defining custom element:", error);
}

// Add a global reference to help with debugging
window.DASHBOARD_BACKUP_CARD_DIRECT = {
  version: "1.0.0",
  defined: !!customElements.get('dashboard-backup-card'),
  element: DashboardBackupCard
};

// Log card registration status for debugging
console.log("Dashboard Backup Card (Direct Import) registration status:", {
  defined: !!customElements.get('dashboard-backup-card'),
  inCustomCards: window.customCards?.some(card => card.type === 'dashboard-backup-card') || false
});
