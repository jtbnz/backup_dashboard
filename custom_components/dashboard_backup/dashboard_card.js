const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

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
  }

  setConfig(config) {
    if (!config.title) {
      config.title = 'Dashboard Backup';
    }
    this.config = config;
  }

  render() {
    if (!this.config) return html``;

    return html`
      <ha-card header="${this.config.title}">
        <div class="card-content">
          <p>${this.config.description || 'Backup and restore your dashboard configuration.'}</p>
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

// Define the element
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
  '%c DASHBOARD-BACKUP-CARD %c Version 1.0.0 ',
  'color: white; background: #3498db; font-weight: 700;',
  'color: #3498db; background: white; font-weight: 700;'
);
