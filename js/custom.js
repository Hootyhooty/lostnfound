// static/js/custom.js

// -------------------------
// Global utility helpers
// -------------------------
function showToast(message, type = "info") {
  const colors = { success: "#28a745", error: "#dc3545", info: "#007bff" };
  const toast = document.createElement("div");
  toast.className = "toast-message";
  toast.style = `position:fixed; top:20px; right:20px; background:${colors[type]}; color:white; padding:10px 15px; border-radius:8px; z-index:2000; box-shadow:0 3px 6px rgba(0,0,0,0.2); font-size:0.9rem;`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.transition = "opacity .4s"; toast.style.opacity = "0"; setTimeout(()=> toast.remove(), 400); }, 2500);
}

function hideModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const bsModal = bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
  bsModal.hide();
}

document.addEventListener("DOMContentLoaded", () => {
  // Reset basket on shop page refresh
  try {
    if (window.location && window.location.pathname === '/shop') {
      localStorage.removeItem('basket');
    }
  } catch (e) {}
  // -------------------------
  // Element references
  // -------------------------
  const loginBtn = document.getElementById("loginBtn");
  const registerBtn = document.getElementById("registerBtn");
  const userDropdown = document.getElementById("userDropdown");
  const userDisplayName = document.getElementById("userDisplayName");
  const logoutLink = document.getElementById("logoutLink");

  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const forgotForm = document.getElementById("forgotForm");

  // Safety: bail if core elements missing
  if (!loginBtn || !userDropdown || !userDisplayName) return;

  // Default UI state
  userDropdown.style.display = "none";
  loginBtn.style.display = "inline-block";
  if (registerBtn) registerBtn.style.display = "inline-block";

  // -------------------------
  // Password toggle utility
  // -------------------------
  function wireToggle(btnId, inputId) {
    const btn = document.getElementById(btnId);
    const inp = document.getElementById(inputId);
    if (!btn || !inp) return;
    btn.addEventListener("click", () => {
      const type = inp.type === "password" ? "text" : "password";
      inp.type = type;
      btn.innerHTML = `<i class="fa fa-${type === "password" ? "eye" : "eye-slash"}"></i>`;
    });
  }
  wireToggle("toggleLoginPassword", "loginPassword");
  wireToggle("toggleRegPassword", "regPassword");
  wireToggle("toggleRegConfirm", "regConfirm");

  // -------------------------
  // Form toggle UI functions
  // -------------------------
  window.showRegister = function () {
    if (loginForm) loginForm.classList.add("d-none");
    if (registerForm) registerForm.classList.remove("d-none");
    if (forgotForm) forgotForm.classList.add("d-none");
    document.getElementById("loginPrompt").classList.add("d-none");
    document.getElementById("registerPrompt").classList.remove("d-none");
    document.getElementById("loginModalLabel").textContent = "Register";
  };

  // Register button click handler
  if (registerBtn) {
    registerBtn.addEventListener("click", (e) => {
      e.preventDefault();
      window.showRegister();
    });
  }

  window.showLogin = function () {
    if (registerForm) registerForm.classList.add("d-none");
    if (forgotForm) forgotForm.classList.add("d-none");
    if (loginForm) loginForm.classList.remove("d-none");
    document.getElementById("registerPrompt").classList.add("d-none");
    document.getElementById("loginPrompt").classList.remove("d-none");
    document.getElementById("loginModalLabel").textContent = "Log in";
  };

  window.showForgot = function () {
    if (loginForm) loginForm.classList.add("d-none");
    if (registerForm) registerForm.classList.add("d-none");
    if (forgotForm) forgotForm.classList.remove("d-none");
    document.getElementById("loginPrompt").classList.add("d-none");
    document.getElementById("registerPrompt").classList.add("d-none");
    document.getElementById("loginModalLabel").textContent = "Forgot Password";
  };
});

document.addEventListener("DOMContentLoaded", () => {
  const toggleLinks = [
    { trigger: "showRegister", show: "registerForm", hide: ["loginForm", "forgotForm", "resetForm"] },
    { trigger: "showLogin", show: "loginForm", hide: ["registerForm", "forgotForm", "resetForm"] },
    { trigger: "showForgot", show: "forgotForm", hide: ["loginForm", "registerForm", "resetForm"] },
    { trigger: "showLoginFromForgot", show: "loginForm", hide: ["forgotForm", "registerForm", "resetForm"] },
  ];

  toggleLinks.forEach(link => {
    const trigger = document.getElementById(link.trigger);
    if (trigger) {
      trigger.addEventListener("click", (e) => {
        e.preventDefault();

        // Hide all other forms
        link.hide.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.classList.add("d-none");
        });

        // Show chosen form
        const showEl = document.getElementById(link.show);
        if (showEl) showEl.classList.remove("d-none");

        // Adjust prompts + title
        document.getElementById("loginPrompt").classList.toggle("d-none", link.show !== "loginForm");
        document.getElementById("registerPrompt").classList.toggle("d-none", link.show === "loginForm");

        const title = document.getElementById("loginModalLabel");
        if (title) {
          if (link.show === "registerForm") title.textContent = "Register";
          else if (link.show === "forgotForm") title.textContent = "Forgot Password";
          else title.textContent = "Log in";
        }
      });
    }
  });
  // -------------------------
  // API fetch with refresh
  // -------------------------
  async function apiFetch(url, options = {}) {
    let accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");

    options.headers = {
      ...(options.headers || {}),
      "Content-Type": "application/json",
      ...(accessToken ? { "Authorization": `Bearer ${accessToken}` } : {})
    };

    let response = await fetch(url, options);

    if (response.status === 401 && refreshToken) {
      // try refresh
      try {
        // Refresh endpoint not implemented yet
        // const refreshRes = await fetch("/api/v1/auth/refresh", {
        //   method: "POST",
        //   headers: { "Content-Type": "application/json" },
        //   body: JSON.stringify({ refresh_token: refreshToken })
        // });

        // Refresh endpoint not implemented - just logout on 401
        logoutUser();
      } catch (err) {
        console.error("Refresh failed", err);
        logoutUser();
      }
    }

    return response;
  }

  // -------------------------
  // Session check
  // -------------------------
  async function checkUserSession() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await apiFetch("/api/v1/users/me", { method: "GET" });
      if (!res.ok) throw new Error("Session invalid");
      const data = await res.json();
      if (data.success && data.user) {
        handleLoginSuccess(data.user);
      } else {
        logoutUser();
      }
    } catch (err) {
      console.warn("Session invalid or expired.", err);
      logoutUser();
    }
  }

  // Call it once on load
  checkUserSession();

  // -------------------------
  // Login form submission
  // -------------------------
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const emailOrUsername = document.getElementById("loginUsername").value.trim();
      const password = document.getElementById("loginPassword").value.trim();

      if (!emailOrUsername || !password) {
        showToast("Please fill in all fields.", "error");
        return;
      }

      try {
        showToast("Logging in...", "info");
        // send both email + identifier to be compatible with either backend variant
        const res = await fetch("/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ identifier: emailOrUsername, email: emailOrUsername, password })
        });

        const data = await res.json();
        if (data.success) {
          const access = data.access_token || data.token || data.jwt || data.token;
          const refresh = data.refresh_token || data.refreshToken || data.refresh;

          if (access) localStorage.setItem("access_token", access);
          if (refresh) localStorage.setItem("refresh_token", refresh);

          // Prefer server's returned user object; otherwise call /me
          if (data.user) {
            handleLoginSuccess(data.user);
            // Check if user is admin and redirect
            let userRole = data.user.role;
            if (userRole && typeof userRole === 'object' && userRole.value) {
              userRole = userRole.value;
            }
            if (userRole === "admin") {
              hideModal("loginModal");
              showToast("✅ Login successful! Redirecting to admin dashboard...", "success");
              setTimeout(() => {
                window.location.href = "/admin";
              }, 1000);
              return;
            }
          } else {
            await checkUserSession();
          }

          hideModal("loginModal");
          showToast("✅ Login successful!", "success");
        } else {
          showToast("❌ " + (data.message || "Login failed"), "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Server error. Please try again.", "error");
      }
    });
  }

  // -------------------------
  // Register form submission
  // -------------------------
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("regName").value.trim();
      const phone = document.getElementById("regPhone").value.trim();
      const email = document.getElementById("regEmail").value.trim();
      const password = document.getElementById("regPassword").value.trim();
      const confirm = document.getElementById("regConfirm").value.trim();

      if (!name || !email || !phone || !password || !confirm) {
        showToast("Please fill in all fields.", "error");
        return;
      }
      if (password !== confirm) {
        showToast("Passwords do not match.", "error");
        document.getElementById("passwordMatchMessage").style.display = "block";
        return;
      }
      document.getElementById("passwordMatchMessage").style.display = "none";

      try {
        showToast("Registering account...", "info");
        const res = await fetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            phone: phone,
            email: email,
            password: password,
            password_confirm: confirm
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast("✅ Registered successfully! Logging you in...", "success");

          // Auto-login after successful registration
          try {
            const loginRes = await fetch("/api/v1/auth/login", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                email: email,
                password: password
              })
            });

            const loginData = await loginRes.json();
            console.log("Login response:", loginData);
            if (loginData.success) {
              const access = loginData.access_token || loginData.token;
              const refresh = loginData.refresh_token;

              console.log("Storing tokens:", { access: !!access, refresh: !!refresh });
              if (access) localStorage.setItem("access_token", access);
              if (refresh) localStorage.setItem("refresh_token", refresh);
              
              // Verify token was stored
              console.log("Token stored:", localStorage.getItem("access_token") ? "Yes" : "No");

              // Update UI to show logged in state
              if (loginData.user) {
                handleLoginSuccess(loginData.user);
              }

              hideModal("loginModal");
              showToast("✅ Registration and login successful!", "success");

              // Verify token is still there before redirecting
              const finalTokenCheck = localStorage.getItem("access_token");
              if (!finalTokenCheck) {
                console.error("Token was lost before redirect!");
                showToast("❌ Login failed. Please try again.", "error");
                return;
              }

              // Redirect to edit profile page
              setTimeout(() => {
                console.log("Redirecting to edit profile page...");
                window.location.href = "/profile/edit";
              }, 2000);
            } else {
              showToast("✅ Registered successfully! Please log in manually.", "success");
              window.showLogin();
            }
          } catch (loginErr) {
            console.error("Auto-login failed:", loginErr);
            showToast("✅ Registered successfully! Please log in manually.", "success");
            window.showLogin();
          }
        } else {
          showToast("❌ " + (data.message || "Registration failed."), "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Server error. Please try again.", "error");
      }
    });
  }

  // -------------------------
  // Forgot password submission
  // -------------------------
  if (forgotForm) {
    forgotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const forgotEmail = document.getElementById("forgotEmail").value.trim();
      if (!forgotEmail) {
        showToast("Please enter your email.", "error");
        return;
      }
      try {
        showToast("Sending reset link...", "info");
        // Forgot password endpoint not implemented yet
        showToast("Forgot password feature not implemented yet", "error");
        return;
        
        /* Commented out until endpoint is implemented
        const res = await fetch("/api/v1/auth/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: forgotEmail })
        });
        const data = await res.json();
        if (data.success) {
          showToast("✅ " + (data.message || "Reset link sent."), "success");
          setTimeout(() => window.showLogin(), 1000);
        } else {
          showToast("❌ " + (data.message || "Failed to send reset link."), "error");
        }
        */
      } catch (err) {
        console.error(err);
        showToast("Server error. Please try again.", "error");
      }
    });
  }

  // -------------------------
  // UI update after login
  // -------------------------
function handleLoginSuccess(user) {
  const loginBtn = document.getElementById("loginBtn");
  const registerBtn = document.getElementById("registerBtn");
  const userDropdown = document.getElementById("userDropdown");
  const userDisplayName = document.getElementById("userDisplayName");
  const userPhoto = document.getElementById("userPhoto");
  const profileLink = document.getElementById("profileLink");

  if (!loginBtn || !userDropdown) return;

  // UI swap
  loginBtn.style.display = "none";
  if (registerBtn) registerBtn.style.display = "none";
  userDropdown.style.display = "inline-block";
  
  // Show logout link
  const logoutLinkEl = document.getElementById("logoutLink");
  if (logoutLinkEl) logoutLinkEl.style.display = "block";

  // Display name + photo
  if (userDisplayName) {
    userDisplayName.textContent = user.name || user.email || "User";
  }
  
  if (userPhoto) {
    const chosen = user.photo;
    userPhoto.src = chosen
      ? (String(chosen).startsWith("http") ? chosen : `/uploads/${chosen}`)
      : "../images/default.jpg";
  }

  // Also update profile page photo if present
  const profileUserPhoto = document.getElementById("profileUserPhoto");
  if (profileUserPhoto) {
    const chosen = user.photo;
    profileUserPhoto.src = chosen
      ? (String(chosen).startsWith("http") ? chosen : `/uploads/${chosen}`)
      : "../images/default.jpg";
  }

  // ✅ Set profile link - admins go to admin page, others go to profile
  if (profileLink) {
    let userRole = user.role;
    if (userRole && typeof userRole === 'object' && userRole.value) {
      userRole = userRole.value;
    }
    
    if (userRole === "admin") {
      // Admin users go to admin dashboard
      profileLink.href = "/admin";
      profileLink.textContent = "Admin Dashboard"; // Update link text for clarity
    } else if (user.profile_slug) {
      // Regular users go to their profile page
      profileLink.href = `/profile/${user.profile_slug}`;
      profileLink.textContent = "Profile"; // Ensure text is correct for regular users
    }
  }
}


  // -------------------------
  // Logout
  // -------------------------
async function logoutUser() {
  // Call server logout endpoint
  const token = localStorage.getItem("access_token");
  if (token) {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
    } catch (err) {
      console.warn("Logout API call failed:", err);
    }
  }

  // Clear local storage
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  // Update UI
  const dropdownEl = document.getElementById("userDropdown");
  if (dropdownEl) dropdownEl.style.display = "none";

  const loginBtnEl = document.getElementById("loginBtn");
  if (loginBtnEl) loginBtnEl.style.display = "inline-block";

  const registerBtnEl = document.getElementById("registerBtn");
  if (registerBtnEl) registerBtnEl.style.display = "inline-block";

  const logoutBtnEl = document.getElementById("logoutBtn");
  if (logoutBtnEl) logoutBtnEl.style.display = "none";

  const logoutLinkEl = document.getElementById("logoutLink");
  if (logoutLinkEl) logoutLinkEl.style.display = "none";

  showToast("Logged out successfully!", "info");
}
// -------------------------
// Separate logout button
// -------------------------
const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", (e) => {
    e.preventDefault();
    logoutUser();
    window.location.href = "/";
  });
}

  // handle dropdown logout (delegated click)
  document.addEventListener("click", (e) => {
    if (e.target && (e.target.id === "logoutLink" || e.target.closest && e.target.closest("#logoutLink"))) {
      e.preventDefault();
      logoutUser();
      window.location.href = "/";
    }
  });

   initializeSearchFunctionality();
  
}); // DOMContentLoaded

// Show Reset Password Form (after clicking reset link)
document.addEventListener("click", function (e) {
  if (e.target && e.target.id === "showResetForm") {
    document.getElementById("forgotForm").classList.add("d-none");
    document.getElementById("resetForm").classList.remove("d-none");
  }
});

document.getElementById("backToLoginFromReset")?.addEventListener("click", (e) => {
  e.preventDefault();
  document.getElementById("resetForm")?.classList.add("d-none");
  document.getElementById("loginForm")?.classList.remove("d-none");
});

document.getElementById("resetForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const password = document.getElementById("resetPassword").value;
  const confirm = document.getElementById("resetConfirm").value;

  if (password !== confirm) {
    document.getElementById("resetMatchMsg")?.style?.setProperty("display", "block");
    return;
  }

  try {
    // Reset password endpoint not implemented yet
    showToast("Reset password feature not implemented yet", "error");
    return;
    
    /* Commented out until endpoint is implemented
    const res = await fetch("/api/v1/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: password }),
    });

    const data = await res.json();
    if (data.success) {
      alert("Password reset successful. Please log in again.");
      document.getElementById("resetForm")?.classList.add("d-none");
      document.getElementById("loginForm")?.classList.remove("d-none");
    } else {
      alert(data.message || "Reset failed.");
    }
    */
  } catch (err) {
    console.error("Reset error:", err);
    alert("An error occurred while resetting password.");
  }
});


// This duplicate forgot password handler is removed - using the one above


// ---------------------------
// Reset Password Flow
// ---------------------------
// This is called when user opens reset-password popup (or link with token)
async function resetPassword(token, newPassword) {
  // Reset password endpoint not implemented yet
  showToast("Reset password feature not implemented yet", "error");
  return false;
  
  /* Commented out until endpoint is implemented
  const res = await fetch("/api/v1/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password: newPassword }),
  });

  const data = await res.json();
  if (data.success) {
    alert("✅ Password reset successful! Please log in again.");
    // You can reopen login modal automatically
    const loginModal = new bootstrap.Modal(document.getElementById("loginModal"));
    loginModal.show();
  } else {
    alert("❌ " + (data.message || "Password reset failed."));
  }
  */
}
// Handle reset form submission
document.getElementById("resetForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const newPass = document.getElementById("resetPassword").value.trim();
  const confirm = document.getElementById("resetConfirm").value.trim();
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (!token) {
    alert("Missing reset token. Please use the link from your email.");
    return;
  }

  if (newPass !== confirm) {
    alert("Passwords do not match!");
    return;
  }

  await resetPassword(token, newPass);
});

function openNav() {
    document.getElementById("myNav").classList.toggle("menu_width");
    document.querySelector(".custom_menu-btn").classList.toggle("menu_btn-style");
}

// -------------------------
// Map Location Picker
// -------------------------
let locationMap = null;
let selectedMarker = null;
let selectedCoordinates = null;
let currentFormType = null; // 'edit' or 'report'
let preselectCoordinates = null; // NEW - for passing preselected lat/lon

// Initialize map when modal is shown
document.addEventListener('DOMContentLoaded', function() {
  const locationMapModal = document.getElementById('locationMapModal');
  if (locationMapModal) {
    locationMapModal.addEventListener('shown.bs.modal', initializeMap);
    locationMapModal.addEventListener('hidden.bs.modal', cleanupMap);
  }
  
  // Handle location map buttons
  const openLocationMapBtn = document.getElementById('openLocationMapBtn');
  if (openLocationMapBtn) {
    openLocationMapBtn.addEventListener('click', () => openLocationMap('edit'));
  }
  
  const openLocationMapReportBtn = document.getElementById('openLocationMapReportBtn');
  if (openLocationMapReportBtn) {
    openLocationMapReportBtn.addEventListener('click', () => openLocationMap('report'));
  }
  
  // Handle map modal buttons
  const useCurrentLocationBtn = document.getElementById('useCurrentLocationBtn');
  if (useCurrentLocationBtn) {
    useCurrentLocationBtn.addEventListener('click', useCurrentLocationOnMap);
  }
  
  const confirmLocationBtn = document.getElementById('confirmLocationBtn');
  if (confirmLocationBtn) {
    confirmLocationBtn.addEventListener('click', confirmLocation);
  }
  
  // Handle search functionality
  const searchLocationBtn = document.getElementById('searchLocationBtn');
  const locationSearchInput = document.getElementById('locationSearchInput');
  
  if (searchLocationBtn) {
    searchLocationBtn.addEventListener('click', searchLocation);
  }
  
  if (locationSearchInput) {
    locationSearchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        searchLocation();
      }
    });
  }
});

function openLocationMap(formType, lat=null, lng=null) {
  currentFormType = formType;
  preselectCoordinates = (lat !== null && lng !== null)
    ? { lat: parseFloat(lat), lng: parseFloat(lng) }
    : null;
  const modal = new bootstrap.Modal(document.getElementById('locationMapModal'));
  modal.show();
}

function initializeMap() {
  if (locationMap) return; // Already initialized

  let center = [40.7128, -74.0060]; // Default to New York
  let zoom = 13;
  if (preselectCoordinates) {
    center = [preselectCoordinates.lat, preselectCoordinates.lng];
    zoom = 15;
  }

  locationMap = L.map('locationMap').setView(center, zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(locationMap);
  // Add marker if viewing preset
  if (preselectCoordinates) {
    addMarker(preselectCoordinates.lat, preselectCoordinates.lng);
    selectedCoordinates = { ...preselectCoordinates };
    document.getElementById('confirmLocationBtn').disabled = false;
  }
  // Add click event to map
  locationMap.on('click', onMapClick);

  // If not preselected, try geolocation as before
  if (!preselectCoordinates) {
    setTimeout(() => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const { latitude, longitude } = position.coords;
            locationMap.setView([latitude, longitude], 15);
            addMarker(latitude, longitude);
            selectedCoordinates = { lat: latitude, lng: longitude };
            document.getElementById('confirmLocationBtn').disabled = false;
          },
          (error) => {
            console.log('Could not get current location:', error);
            // Keep default location
          }
        );
      }
    }, 500);
  }
}

function onMapClick(e) {
  const { lat, lng } = e.latlng;
  addMarker(lat, lng);
  selectedCoordinates = { lat, lng };
  document.getElementById('confirmLocationBtn').disabled = false;
}

function addMarker(lat, lng) {
  // Remove existing marker
  if (selectedMarker) {
    locationMap.removeLayer(selectedMarker);
  }
  
  // Add new marker
  selectedMarker = L.marker([lat, lng], {
    draggable: true
  }).addTo(locationMap);
  
  // Update coordinates when marker is dragged
  selectedMarker.on('dragend', function(e) {
    const newPos = e.target.getLatLng();
    selectedCoordinates = { lat: newPos.lat, lng: newPos.lng };
  });
}

function useCurrentLocationOnMap() {
  if (!navigator.geolocation) {
    showToast("Geolocation is not supported by this browser.", "error");
    return;
  }
  
  const btn = document.getElementById('useCurrentLocationBtn');
  const originalText = btn.innerHTML;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>Getting Location...';
  btn.disabled = true;
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      // Center map on current location with proper zoom
      locationMap.setView([latitude, longitude], 15);
      addMarker(latitude, longitude);
      selectedCoordinates = { lat: latitude, lng: longitude };
      document.getElementById('confirmLocationBtn').disabled = false;
      showToast("Location found!", "success");
      
      btn.innerHTML = originalText;
      btn.disabled = false;
    },
    (error) => {
      console.error('Geolocation error:', error);
      showToast("Could not get your location. Please click on the map instead.", "error");
      
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  );
}

async function confirmLocation() {
  if (!selectedCoordinates) {
    showToast("Please select a location on the map first.", "error");
    return;
  }
  
  const btn = document.getElementById('confirmLocationBtn');
  const originalText = btn.innerHTML;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>Getting Address...';
  btn.disabled = true;
  
  try {
    // Reverse geocode the selected coordinates
    const address = await reverseGeocodeFromCoords(selectedCoordinates.lat, selectedCoordinates.lng);
    
    // Fill the appropriate form based on current form type
    if (currentFormType === 'edit') {
      fillEditProfileFields(address);
    } else if (currentFormType === 'report') {
      fillReportFormFields(address);
    }
    
    showToast("Address filled successfully!", "success");
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('locationMapModal'));
    modal.hide();
    
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    showToast("Could not get address for selected location. Please try again.", "error");
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

async function reverseGeocodeFromCoords(lat, lng) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'LostAndFound-App/1.0'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error("Reverse geocoding failed");
    }
    
    const data = await response.json();
    return parseAddressData(data);
  } catch (error) {
    console.error("Reverse geocoding error:", error);
    throw error;
  }
}

function parseAddressData(data) {
  const address = data.address || {};
  
  return {
    address_line1: [
      address.house_number,
      address.road
    ].filter(Boolean).join(" "),
    address_line2: address.suburb || "",
    city: address.city || address.town || address.village || "",
    state: address.state || "",
    zipcode: address.postcode || "",
    country: address.country || "",
    // For report form
    address: [
      address.house_number,
      address.road
    ].filter(Boolean).join(" "),
    city_town: address.city || address.town || address.village || "",
    state_province: address.state || ""
  };
}

function fillEditProfileFields(address) {
  const fields = {
    'address_line1': address.address_line1,
    'address_line2': address.address_line2,
    'city': address.city,
    'state': address.state,
    'zipcode': address.zipcode
  };
  
  Object.entries(fields).forEach(([fieldId, value]) => {
    const field = document.getElementById(fieldId);
    if (field && value) {
      field.value = value;
    }
  });
  
  // Handle country dropdown
  const countrySelect = document.getElementById("country");
  if (countrySelect && address.country) {
    const countryOptions = Array.from(countrySelect.options);
    const matchingOption = countryOptions.find(option => 
      option.value.toLowerCase().includes(address.country.toLowerCase()) ||
      address.country.toLowerCase().includes(option.value.toLowerCase())
    );
    
    if (matchingOption) {
      countrySelect.value = matchingOption.value;
    } else if (address.country) {
      countrySelect.value = "Other";
    }
  }
}

function fillReportFormFields(address) {
  const fields = {
    'address': address.address,
    'city_town': address.city_town,
    'state_province': address.state_province,
    'zipcode': address.zipcode,
    'country': address.country
  };

  Object.entries(fields).forEach(([fieldId, value]) => {
    const field = document.getElementById(fieldId);
    if (field && value) {
      field.value = value;
    }
  });
  // Set latitude/longitude if selectedCoordinates present
  if (window.selectedCoordinates) {
    const latField = document.getElementById('latitude');
    const lngField = document.getElementById('longitude');
    if (latField && lngField) {
      latField.value = window.selectedCoordinates.lat;
      lngField.value = window.selectedCoordinates.lng;
    }
  }
}

async function searchLocation() {
  const searchInput = document.getElementById('locationSearchInput');
  const searchBtn = document.getElementById('searchLocationBtn');
  
  if (!searchInput || !searchInput.value.trim()) {
    showToast("Please enter a location to search for.", "error");
    return;
  }
  
  const originalText = searchBtn.innerHTML;
  searchBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
  searchBtn.disabled = true;
  
  try {
    const query = searchInput.value.trim();
    const results = await geocodeLocation(query);
    
    if (results && results.length > 0) {
      const result = results[0]; // Use first result
      const lat = parseFloat(result.lat);
      const lng = parseFloat(result.lon);
      
      // Center map on search result with proper zoom
      locationMap.setView([lat, lng], 15);
      addMarker(lat, lng);
      selectedCoordinates = { lat, lng };
      document.getElementById('confirmLocationBtn').disabled = false;
      
      showToast(`Found: ${result.display_name}`, "success");
    } else {
      showToast("No locations found. Please try a different search term.", "error");
    }
  } catch (error) {
    console.error("Search error:", error);
    showToast("Search failed. Please try again.", "error");
  } finally {
    searchBtn.innerHTML = originalText;
    searchBtn.disabled = false;
  }
}

async function geocodeLocation(query) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'LostAndFound-App/1.0'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error("Geocoding failed");
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Geocoding error:", error);
    throw error;
  }
}

function cleanupMap() {
  if (locationMap) {
    locationMap.remove();
    locationMap = null;
  }
  selectedMarker = null;
  selectedCoordinates = null;
  document.getElementById('confirmLocationBtn').disabled = true;
  
  // Clear search input
  const searchInput = document.getElementById('locationSearchInput');
  if (searchInput) {
    searchInput.value = '';
  }
}

// ===================================== */
//  SEARCH FUNCTIONALITY                 */
// ===================================== */

// Global variables for search functionality
let currentSearchResults = [];
let currentPage = 1;
let totalPages = 1;
let searchParams = {};

// Search functionality will be initialized in the main DOMContentloaded listener

function initializeSearchFunctionality() {
  // Toggle advanced search
  const toggleAdvancedSearch = document.getElementById('toggleAdvancedSearch');
  const advancedSearchContainer = document.getElementById('advancedSearchContainer');
  
  if (toggleAdvancedSearch && advancedSearchContainer) {
    toggleAdvancedSearch.addEventListener('click', function() {
      const isVisible = advancedSearchContainer.style.display !== 'none';
      advancedSearchContainer.style.display = isVisible ? 'none' : 'block';
      
      const icon = this.querySelector('i');
      if (icon) {
        icon.className = isVisible ? 'fa fa-chevron-down' : 'fa fa-chevron-up';
      }
    });
  }

  // Zipcode options toggle
  const zipcodeOptionsBtn = document.getElementById('zipcodeOptionsBtn');
  const zipcodeOptions = document.getElementById('zipcodeOptions');
  
  if (zipcodeOptionsBtn && zipcodeOptions) {
    zipcodeOptionsBtn.addEventListener('click', function() {
      const isVisible = zipcodeOptions.style.display !== 'none';
      zipcodeOptions.style.display = isVisible ? 'none' : 'block';
    });
  }

  // Quick search form submission
  const quickSearchForm = document.getElementById('quickSearchForm');
  if (quickSearchForm) {
    quickSearchForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleQuickSearch();
    });
  }

  // Advanced search form submission
  const advancedSearchForm = document.getElementById('advancedSearchForm');
  if (advancedSearchForm) {
    advancedSearchForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleAdvancedSearch();
    });
  }

  // Results search functionality
  const resultsSearchBtn = document.getElementById('resultsSearchBtn');
  if (resultsSearchBtn) {
    resultsSearchBtn.addEventListener('click', function() {
      const keyword = document.getElementById('resultsKeyword').value;
      if (keyword.trim()) {
        searchParams.keyword = keyword.trim();
        performSearch();
      }
    });
  }

  // Quick search dropdown change handler
  const quickSearchType = document.getElementById('quickSearchType');
  if (quickSearchType) {
    quickSearchType.addEventListener('change', function() {
      const statusField = document.getElementById('status');
      if (statusField) {
        if (this.value === 'lost') {
          statusField.value = 'Lost';
        } else if (this.value === 'found') {
          statusField.value = 'Found';
        }
      }
    });
  }
}

function handleQuickSearch() {
  // Check if user is logged in
  if (!isUserLoggedIn()) {
    showLoginRequired();
    return;
  }

  const keyword = document.getElementById('quickKeyword').value.trim();
  const searchType = document.getElementById('quickSearchType').value;

  if (!keyword) {
    showAlert('Please enter a search keyword.', 'warning');
    return;
  }

  // Build search parameters based on quick search type
  searchParams = {
    keyword: keyword,
    page: 1
  };

  switch (searchType) {
    case 'near_me':
      searchParams.near_me = true;
      break;
    case 'by_venue':
      searchParams.by_venue = true;
      break;
    case 'lost':
      searchParams.status = 'Lost';
      break;
    case 'found':
      searchParams.status = 'Found';
      break;
  }

  performSearch();
}

function handleAdvancedSearch() {
  // Check if user is logged in
  if (!isUserLoggedIn()) {
    showLoginRequired();
    return;
  }

  // Collect all form data
  const formData = {
    status: document.getElementById('status').value.trim(),
    keyword: document.getElementById('keyword').value.trim(),
    category: document.getElementById('category').value.trim(),
    subCategory: document.getElementById('subCategory').value.trim(),
    country: document.getElementById('country').value.trim(),
    state: document.getElementById('state').value.trim(),
    city: document.getElementById('city').value.trim(),
    zipcode: document.getElementById('zipcode').value.trim(),
    page: 1
  };

  // Add radius if zipcode is provided and radius is selected
  const selectedRadius = document.querySelector('input[name="radius"]:checked');
  if (formData.zipcode && selectedRadius) {
    formData.radius = parseInt(selectedRadius.value);
  }

  // Remove empty fields
  searchParams = Object.fromEntries(
    Object.entries(formData).filter(([_, value]) => value !== '')
  );

  // If no parameters provided, search all items
  if (Object.keys(searchParams).length === 1 && searchParams.page) {
    searchParams = { page: 1 };
  }

  performSearch();
}

async function performSearch() {
  try {
    showLoadingSpinner();
    
    const response = await fetch('/api/v1/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify(searchParams)
    });

    if (!response.ok) {
      if (response.status === 401) {
        showLoginRequired();
        return;
      }
      throw new Error(`Search failed: ${response.status}`);
    }

    const data = await response.json();
    currentSearchResults = data.results || [];
    currentPage = data.page || 1;
    totalPages = data.total_pages || 1;

    displaySearchResults();
    hideLoadingSpinner();

  } catch (error) {
    console.error('Search error:', error);
    showAlert('Search failed. Please try again.', 'error');
    hideLoadingSpinner();
  }
}

function displaySearchResults() {
  const resultsContainer = document.getElementById('searchResults');
  const tableBody = document.getElementById('resultsTableBody');
  const paginationContainer = document.getElementById('resultsPagination');

  if (!resultsContainer || !tableBody || !paginationContainer) {
    return;
  }

  // Show results container
  resultsContainer.style.display = 'block';

  // Populate table
  tableBody.innerHTML = '';
  
  if (currentSearchResults.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted">
          <i class="fa fa-search"></i> No results found
        </td>
      </tr>
    `;
  } else {
    currentSearchResults.forEach(item => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>
          <img src="${item.image_url || '/static/images/default.jpg'}" 
               alt="Item" class="item-thumbnail" 
               style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;">
        </td>
        <td>${formatDate(item.created_at)}</td>
        <td>
          <span class="badge bg-primary">${item.category}</span>
          ${item.sub_category ? `<br><small class="text-muted">${item.sub_category}</small>` : ''}
        </td>
        <td>
          <a href="/item/${item.slug}"><strong>${item.title}</strong></a>
          <br><small class="text-muted">${item.description}</small>
        </td>
        <td>
          <small>
            ${item.city}, ${item.state}<br>
            <span class="text-muted">${item.country}</span>
          </small>
        </td>
      `;
      tableBody.appendChild(row);
    });
  }

  // Populate pagination
  generatePagination(paginationContainer);
}

function generatePagination(container) {
  container.innerHTML = '';

  if (totalPages <= 1) return;

  // Previous button
  const prevLi = document.createElement('li');
  prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
  prevLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">Previous</a>`;
  container.appendChild(prevLi);

  // Page numbers
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);

  if (startPage > 1) {
    const firstLi = document.createElement('li');
    firstLi.className = 'page-item';
    firstLi.innerHTML = `<a class="page-link" href="#" data-page="1">1</a>`;
    container.appendChild(firstLi);

    if (startPage > 2) {
      const ellipsisLi = document.createElement('li');
      ellipsisLi.className = 'page-item disabled';
      ellipsisLi.innerHTML = '<span class="page-link">...</span>';
      container.appendChild(ellipsisLi);
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    const li = document.createElement('li');
    li.className = `page-item ${i === currentPage ? 'active' : ''}`;
    li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
    container.appendChild(li);
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      const ellipsisLi = document.createElement('li');
      ellipsisLi.className = 'page-item disabled';
      ellipsisLi.innerHTML = '<span class="page-link">...</span>';
      container.appendChild(ellipsisLi);
    }

    const lastLi = document.createElement('li');
    lastLi.className = 'page-item';
    lastLi.innerHTML = `<a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>`;
    container.appendChild(lastLi);
  }

  // Next button
  const nextLi = document.createElement('li');
  nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
  nextLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">Next</a>`;
  container.appendChild(nextLi);

  // Add click handlers
  container.addEventListener('click', function(e) {
    e.preventDefault();
    const pageLink = e.target.closest('.page-link');
    if (pageLink && !pageLink.parentElement.classList.contains('disabled')) {
      const page = parseInt(pageLink.dataset.page);
      if (page && page !== currentPage) {
        searchParams.page = page;
        performSearch();
      }
    }
  });
}

function isUserLoggedIn() {
  const token = getAuthToken();
  return token && token !== 'null' && token !== 'undefined';
}

function getAuthToken() {
  return localStorage.getItem('access_token');
}

function showLoginRequired() {
  showAlert('Please login to perform searches.', 'warning');
  // Optionally trigger login modal
  const loginBtn = document.getElementById('loginBtn');
  if (loginBtn) {
    loginBtn.click();
  }
}

function showAlert(message, type = 'info') {
  // Create alert element
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
  alertDiv.style.position = 'fixed';
  alertDiv.style.top = '20px';
  alertDiv.style.right = '20px';
  alertDiv.style.zIndex = '9999';
  alertDiv.style.minWidth = '300px';
  
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(alertDiv);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.parentNode.removeChild(alertDiv);
    }
  }, 5000);
}

function showLoadingSpinner() {
  const spinner = document.createElement('div');
  spinner.id = 'searchSpinner';
  spinner.className = 'text-center p-4';
  spinner.innerHTML = `
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Searching...</span>
    </div>
    <p class="mt-2">Searching...</p>
  `;
  spinner.style.position = 'fixed';
  spinner.style.top = '50%';
  spinner.style.left = '50%';
  spinner.style.transform = 'translate(-50%, -50%)';
  spinner.style.zIndex = '9999';
  spinner.style.background = 'rgba(255, 255, 255, 0.9)';
  spinner.style.padding = '20px';
  spinner.style.borderRadius = '10px';
  spinner.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';

  document.body.appendChild(spinner);
}

function hideLoadingSpinner() {
  const spinner = document.getElementById('searchSpinner');
  if (spinner) {
    spinner.remove();
  }
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// ===============================
// SHOP BASKET LOGIC (for shop.html)
// ===============================
(function(){
  if (!document.querySelector('.shop_section')) return; // Only run on shop

  // Util
  function getBasket() {
    try {
      return JSON.parse(localStorage.getItem('lf_basket') || '{}');
    } catch { return {}; }
  }
  function saveBasket(basket) {
    localStorage.setItem('lf_basket', JSON.stringify(basket));
  }

  function basketTotalItems(basket) {
    let sum = 0;
    Object.values(basket).forEach(x => sum += x.qty);
    return sum;
  }
  function basketTotalPrice(basket) {
    let tot = 0;
    Object.values(basket).forEach(x => tot += x.qty * x.price);
    return tot.toFixed(2);
  }

  // UI update
  function renderBasketCount() {
    let basket = getBasket();
    document.getElementById('basketCount').textContent = basketTotalItems(basket);
  }
  function renderBasketModal() {
    let basket = getBasket();
    let html = '';
    if (Object.keys(basket).length === 0) {
      html = '<p class="text-muted">Your basket is empty.</p>';
    } else {
      html = '<ul class="list-group mb-3">';
      Object.values(basket).forEach(item => {
        html += `
          <li class="list-group-item d-flex align-items-center justify-content-between">
            <span>
              <strong>
                ${item.name}
              </strong> x <span class="badge bg-light text-dark">${item.qty}</span>
              <span class="ms-2">@$${item.price}</span>
            </span>
            <span>
              <button class="btn btn-sm btn-outline-secondary me-1" data-act="dec" data-code="${item.product_code}"><i class="fa fa-minus"></i></button>
              <button class="btn btn-sm btn-outline-secondary me-1" data-act="inc" data-code="${item.product_code}"><i class="fa fa-plus"></i></button>
              <button class="btn btn-sm btn-outline-danger" data-act="rm" data-code="${item.product_code}"><i class="fa fa-trash"></i></button>
            </span>
          </li>`;
      });
      html += '</ul>';
    }
    document.getElementById('basketItems').innerHTML = html;
    document.getElementById('basketTotal').textContent = basketTotalPrice(basket);
  }

  // Add to basket
  document.querySelectorAll('.add-to-basket').forEach(btn => {
    btn.addEventListener('click', function(e){
      let token = localStorage.getItem('access_token');
      if (!token) {
        e.preventDefault();
        if (window.showLogin) { 
          if (window.showToast) showToast('Please log in to add to basket.', 'error');
          window.showLogin();
        }
        return false;
      }
      let code = this.dataset.item, name = this.dataset.name, price = parseFloat(this.dataset.price);
      let basket = getBasket();
      if (basket[code]) {
        basket[code].qty += 1;
      } else {
        basket[code] = { product_code: code, name, price, qty: 1 };
      }
      saveBasket(basket);
      renderBasketCount();
    });
  });

  // Show basket modal
  let basketBtn = document.getElementById('basketBtn');
  if (basketBtn) basketBtn.addEventListener('click', function(){
    renderBasketModal();
    new bootstrap.Modal(document.getElementById('basketModal')).show();
  });

  // Handle quantity/increment/remove buttons
  document.getElementById('basketModal').addEventListener('click', function(e){
    let tgt = e.target.closest('button[data-act]');
    if (!tgt) return;
    let code = tgt.dataset.code, act = tgt.dataset.act, basket = getBasket();
    if (!basket[code]) return;
    if (act==='inc') basket[code].qty++;
    else if (act==='dec') basket[code].qty > 1 ? basket[code].qty-- : delete basket[code];
    else if (act==='rm') delete basket[code];
    saveBasket(basket);
    renderBasketCount();
    renderBasketModal();
  });

  // Submit basket to real providers
  async function checkoutStripe(items){
    const res = await fetch('/api/checkout/stripe',{
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({items})
    });
    const data = await res.json();
    if (data && data.url){ window.location = data.url; } else { alert('Stripe init failed'); }
  }

  async function checkoutPaypal(items){
    const res = await fetch('/api/paypal/create-order',{
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({items})
    });
    const data = await res.json();
    if (data && data.approve_url){ window.location = data.approve_url; }
    else { alert('PayPal init failed'); }
  }

  function beginCheckout(method){
    const basket = getBasket();
    if (!Object.keys(basket).length){ alert('Basket is empty.'); return; }
    const items = Object.values(basket);
    if (method==='stripe') return checkoutStripe(items);
    if (method==='paypal') return checkoutPaypal(items);
  }

  document.getElementById('paypalCheckout').addEventListener('click', ()=>beginCheckout('paypal'));
  document.getElementById('stripeCheckout').addEventListener('click', ()=>beginCheckout('stripe'));

  // Initial count on page load
  renderBasketCount();
})();

document.getElementById('reportPageBtn')?.addEventListener('click', function(e){
  e.preventDefault();
  let token = localStorage.getItem('access_token');
  if (!token) { window.showLogin && window.showLogin(); return; }
  window.location.href = '/report';
});

// Handler for report items image (login required)
document.getElementById('boxReportLink')?.addEventListener('click', function(e){
  e.preventDefault();
  let token = localStorage.getItem('access_token');
  if (!token) {
    // Try login modal first
    if (window.showLogin) {
      window.showLogin();
    } else {
      // Fallback to custom alert centered on page
      let existing = document.getElementById('loginRequiredAlert');
      if (existing) existing.remove();
      let alert = document.createElement('div');
      alert.id = 'loginRequiredAlert';
      alert.className = 'alert alert-warning text-center fade show';
      alert.style = 'position:fixed;top:45%;left:50%;transform:translate(-50%,-50%);z-index:3000;width:320px;padding:27px;font-size:1.1rem;box-shadow:0 7px 24px rgba(0,0,0,0.06);background:#fff;';
      alert.innerHTML = `<strong>Login required</strong><br>Please login to report items.<br><button class='btn btn-sm btn-secondary mt-2' onclick='this.parentElement.remove()'>Close</button>`;
      document.body.appendChild(alert);
    }
    return;
  }
  window.location.href = '/report-lost-found';
});
document.getElementById('boxShopLink')?.addEventListener('click', function(e){
  e.preventDefault();
  let token = localStorage.getItem('access_token');
  if (!token) { window.showLogin && window.showLogin(); return; }
  window.location.href = '/shop';
});

