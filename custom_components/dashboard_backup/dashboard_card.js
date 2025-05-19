class DashboardBackupCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.title) {
      config.title = 'Dashboard Backup';
    }
    this.config = config;

    this.shadowRoot.innerHTML = `
      <ha-card header="${config.title}">
        <div class="card-content">
          <p>${config.description || 'Backup and restore your dashboard configuration.'}</p>
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

  _createBackup() {
    const dashboardId = this.config.dashboard_id || 'lovelace';
    this._hass.callService('dashboard_backup', 'create_backup', {
      dashboard_id: dashboardId
    });
    this._showToast('Creating dashboard backup...');
  }

  _restoreBackup() {
    const dashboardId = this.config.dashboard_id || 'lovelace';
    this._hass.callService('dashboard_backup', 'restore_backup', {
      dashboard_id: dashboardId
    });
    this._showToast('Restoring dashboard from backup...');
  }

  _showToast(message) {
    const event = new CustomEvent('hass-notification', {
      detail: { message },
      bubbles: true,
      composed: true
    });
    this.dispatchEvent(event);
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('dashboard-backup-card', DashboardBackupCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'dashboard-backup-card',
  name: 'Dashboard Backup Card',
  description: 'A card that provides buttons to backup and restore your dashboard configuration.'
});
