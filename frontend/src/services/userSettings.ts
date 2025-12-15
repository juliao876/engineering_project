export type UserSettings = {
  bioEnabled: boolean;
  bioText: string;
  figmaClientId: string;
  figmaClientSecret: string;
  avatarUrl?: string;
};

const STORAGE_KEY = "user_settings";

const defaultSettings: UserSettings = {
  bioEnabled: false,
  bioText: "",
  figmaClientId: "",
  figmaClientSecret: "",
  avatarUrl: "",
};

export function loadUserSettings(): UserSettings {
  if (typeof localStorage === "undefined") {
    return { ...defaultSettings };
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...defaultSettings };
    const parsed = JSON.parse(raw) as Partial<UserSettings>;
    return {
      ...defaultSettings,
      ...parsed,
    };
  } catch (error) {
    console.error("[Settings] Failed to parse user settings", error);
    return { ...defaultSettings };
  }
}

export function saveUserSettings(settings: UserSettings) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function updateUserSettings(partial: Partial<UserSettings>): UserSettings {
  const current = loadUserSettings();
  const updated = { ...current, ...partial };
  saveUserSettings(updated);
  return updated;
}