// Try multiple methods to get LitElement
let LitElement, html, css;
try {
  // Method 1: Get from ha-panel-lovelace
  const HaPanelLovelace = customElements.get("ha-panel-lovelace");
  if (HaPanelLovelace) {
    LitElement = Object.getPrototypeOf(HaPanelLovelace);
    html = LitElement.prototype.html;
    css = LitElement.prototype.css;
    console.log("Dashboard Backup Card: Using LitElement from ha-panel-lovelace");
  } else {
    throw new Error("ha-panel-lovelace not found");
  }
} catch (e) {
  console.warn("Dashboard Backup Card: Could not get LitElement from ha-panel-lovelace:", e);
  
  try {
    // Method 2: Get from card-tools
    if (window.cardTools) {
      ({ LitElement, html, css } = window.cardTools);
      console.log("Dashboard Backup Card: Using LitElement from card-tools");
    } else {
      throw new Error("card-tools not found");
    }
  } catch (e) {
    console.warn("Dashboard Backup Card: Could not get LitElement from card-tools:", e);
    
    try {
      // Method 3: Get from another common element
      const commonElement = customElements.get("hui-view") || customElements.get("hui-card-element-editor");
      if (commonElement) {
        LitElement = Object.getPrototypeOf(commonElement);
        html = LitElement.prototype.html;
        css = LitElement.prototype.css;
        console.log("Dashboard Backup Card: Using LitElement from common element");
      } else {
        throw new Error("Common elements not found");
      }
    } catch (e) {
      console.warn("Dashboard Backup Card: Could not get LitElement from common elements:", e);
      
      // Method 4: Fallback to direct import if available in the environment
      try {
        if (window.lit && window.lit.html && window.lit.css) {
          LitElement = window.lit.LitElement;
          html = window.lit.html;
          css = window.lit.css;
          console.log("Dashboard Backup Card: Using LitElement from window.lit");
        } else {
          throw new Error("window.lit not found");
        }
      } catch (e) {
        console.error("Dashboard Backup Card: All methods to get LitElement failed:", e);
        // Create a notification in the UI
        const event = new CustomEvent("hass-notification", {
          detail: {
            message: "Dashboard Backup Card: Failed to load LitElement. The card may not work properly.",
            duration: 0,
          },
          bubbles: true,
          composed: true,
        });
        document.querySelector("home-assistant").dispatchEvent(event);
      }
    }
  }
}

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
          <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <ha-icon icon="mdi:backup-restore" style="width: 40px; height: 40px; margin-right: 16px;"></ha-icon>
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
    console.log("Dashboard Backup Card: Defining custom element 'dashboard-backup-card'");
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
  } else {
    console.log("Dashboard Backup Card: Custom element 'dashboard-backup-card' already defined");
  }
} catch (error) {
  console.error("Dashboard Backup Card: Error defining custom element:", error);
  
  // Create a notification in the UI
  setTimeout(() => {
    try {
      const event = new CustomEvent("hass-notification", {
        detail: {
          message: "Dashboard Backup Card: Error defining custom element. Please check the browser console for details.",
          duration: 0,
        },
        bubbles: true,
        composed: true,
      });
      document.querySelector("home-assistant")?.dispatchEvent(event);
    } catch (e) {
      console.error("Dashboard Backup Card: Could not create notification:", e);
    }
  }, 2000);
}

// Add a global reference to help with debugging
window.DASHBOARD_BACKUP_CARD = {
  version: "1.0.0",
  defined: !!customElements.get('dashboard-backup-card'),
  element: DashboardBackupCard
};

// Log card registration status for debugging
console.log("Dashboard Backup Card registration status:", {
  defined: !!customElements.get('dashboard-backup-card'),
  inCustomCards: window.customCards?.some(card => card.type === 'dashboard-backup-card') || false
});
