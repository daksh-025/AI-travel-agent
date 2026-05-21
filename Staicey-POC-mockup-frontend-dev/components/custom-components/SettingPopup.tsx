"use client";
import { useState, useEffect } from "react";
import { X, User, Settings, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUser } from "@/app/context/UserContext";
import { updateUserProfile, changeUserPassword, getUserProfile } from "@/lib/api";

interface SettingPopupProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: string;
}

export default function SettingPopup({ isOpen, onClose, initialTab = "general" }: SettingPopupProps) {
  const { user, updateUser } = useUser();
  const [activeTab, setActiveTab] = useState(initialTab);
  
  // General settings state
  const [language, setLanguage] = useState("");
  const [homeLocation, setHomeLocation] = useState("");
  const [currency, setCurrency] = useState("");
  
  // Account settings state
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Load fresh user profile data when popup opens
  const loadUserProfile = async () => {
    if (!user) return;
    
    try {
      const result = await getUserProfile();
      if (result.data && !result.error) {
        // Update user context with fresh data from API
        updateUser(result.data);
      }
    } catch (error) {
      console.error("Error loading user profile:", error);
    }
  };

  // Initialize firstName, email, language, location, currency, and preferences from user context
  useEffect(() => {
    if (user) {
      setFirstName(user.username || "");
      setEmail(user.email || "");
      setLanguage(user.language || "");
      setHomeLocation(user.location?.city || "");
      setCurrency(user.currency || "");
      
      // Initialize preferences if available
      if (user.preferences) {
        setAdults(user.preferences.adults || "2");
        setChildren(user.preferences.children || "0");
        setChildrenAgeList(user.preferences.childrenAgeList || []);
        setTripType(user.preferences.tripType || "holiday");
        setOtherTripType(user.preferences.otherTripType || "");
        setBudget(user.preferences.budget || "");
        setBudgetType(user.preferences.budgetType || "flexible");
        setMinStarRating(user.preferences.minStarRating || "4");
        setSelectedPreferences(user.preferences.searchPreferences || []);
      }
    }
  }, [user]);

  // Load fresh profile data when popup opens
  useEffect(() => {
    if (isOpen) {
      loadUserProfile();
      setActiveTab(initialTab); // Reset to initial tab when opened
    }
  }, [isOpen, initialTab]);

  // Save changes functionality
  const handleSaveChanges = async () => {
    if (!user) {
      setSaveMessage("No user data available");
      return;
    }
    
    if (!firstName.trim()) {
      setSaveMessage("Username cannot be empty");
      return;
    }
    
    setIsSaving(true);
    setSaveMessage("");
    
    try {
      // Call backend API to update profile
      const result = await updateUserProfile({
        username: firstName.trim(),
        email: user.email, // Keep email safe - send current email
        language: language,
        location: {
          city: homeLocation,
          country: user.location?.country || "", // Keep existing country or empty
        },
        currency: currency,
        preferences: {
          adults: adults,
          children: children,
          childrenAgeList: childrenAgeList,
          tripType: tripType,
          otherTripType: otherTripType,
          budget: budget,
          budgetType: budgetType,
          minStarRating: minStarRating,
          searchPreferences: selectedPreferences,
        },
      });
      
      if (result.error) {
        setSaveMessage(result.error);
        return;
      }
      
      // Update local user context with new data
      const updatedUser = {
        ...user,
        username: firstName.trim(),
        language: language,
        location: {
          city: homeLocation,
          country: user.location?.country || "",
        },
        currency: currency,
        preferences: {
          adults: adults,
          children: children,
          childrenAgeList: childrenAgeList,
          tripType: tripType,
          otherTripType: otherTripType,
          budget: budget,
          budgetType: budgetType,
          minStarRating: minStarRating,
          searchPreferences: selectedPreferences,
        },
        // Email remains unchanged
      };
      
      updateUser(updatedUser);
      setSaveMessage("Changes saved successfully!");
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveMessage("");
      }, 3000);
    } catch (error) {
      console.error("Error saving changes:", error);
      setSaveMessage("Failed to save changes. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  // Password change functionality
  const handlePasswordChange = async () => {
    if (!currentPassword.trim()) {
      setSaveMessage("Current password is required");
      return;
    }
    
    if (!newPassword.trim()) {
      setSaveMessage("New password is required");
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setSaveMessage("New passwords do not match");
      return;
    }
    
    if (newPassword.length < 6) {
      setSaveMessage("New password must be at least 6 characters");
      return;
    }
    
    setIsChangingPassword(true);
    setSaveMessage("");
    
    try {
      const result = await changeUserPassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      
      if (result.error) {
        setSaveMessage(result.error);
        return;
      }
      
      setSaveMessage("Password changed successfully!");
      
      // Clear password fields
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveMessage("");
      }, 3000);
    } catch (error) {
      console.error("Error changing password:", error);
      setSaveMessage("Failed to change password. Please try again.");
    } finally {
      setIsChangingPassword(false);
    }
  };
  
  // Preferences settings state
  const [adults, setAdults] = useState("2");
  const [children, setChildren] = useState("0");
  const [childrenAgeList, setChildrenAgeList] = useState<string[]>([]);
  const [tripType, setTripType] = useState("holiday");
  const [budget, setBudget] = useState("");
  const [budgetType, setBudgetType] = useState("flexible");
  const [minStarRating, setMinStarRating] = useState("4");
  // const [searchPreferences, setSearchPreferences] = useState("");
  const [otherTripType, setOtherTripType] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);
  
  // Save operation state
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  
  // Password change state
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const searchPreferencesOptions = [
    {
      label: "Free parking",
      value: "freeParking",
    },
    {
      label: "Parking",
      value: "parking",
    },
    {
      label: "Indoor pool",
      value: "indoorPool",
    },
    {
      label: "Outdoor pool",
      value: "outdoorPool",
    },
    {
      label: "Pool",
      value: "pool",
    },
    {
      label: "Fitness center",
      value: "fitnessCenter",
    },
    {
      label: "Restaurant",
      value: "restaurant",
    },
    {
      label: "Free breakfast",
      value: "freeBreakfast",
    },
    {
      label: "Spa",
      value: "spa",
    },
    {
      label: "Beach access",
      value: "beachAccess",
    },
    {
      label: "Child-friendly",
      value: "childFriendly",
    },
    {
      label: "Bar",
      value: "bar",
    },
    {
      label: "Pet-friendly",
      value: "petFriendly",
    },
    {
      label: "Room service",
      value: "roomService",
    },
    {
      label: "Free Wi-Fi",
      value: "freeWiFi",
    },
    {
      label: "Air-conditioned",
      value: "airConditioned",
    },
    {
      label: "All-inclusive available",
      value: "allInclusiveAvailable",
    },
    {
      label: "Wheelchair accessible",
      value: "wheelchairAccessible",
    },
    {
      label: "EV charger",
      value: "evCharger",
    },
  ];

  const filteredOptions = searchPreferencesOptions.filter(option =>
    option.label.toLowerCase().includes(searchInput.toLowerCase()) &&
    !selectedPreferences.includes(option.value)
  );

  const handleAddPreference = (value: string) => {
    if (!selectedPreferences.includes(value)) {
      setSelectedPreferences([...selectedPreferences, value]);
      setSearchInput("");
    }
  };

  const handleRemovePreference = (value: string) => {
    setSelectedPreferences(selectedPreferences.filter(pref => pref !== value));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-[26px] w-full max-w-3xl max-h-[90vh] overflow-hidden">
        {/* Content with Sidebar Layout */}
        <div className="flex flex-col lg:flex-row h-[calc(90vh-120px)]">
          {/* Left Sidebar - Hidden on mobile, shown on desktop */}
          <div className="hidden lg:block w-48 border-r border-gray-200 bg-gray-50">
            <div className="p-4">
              <Button variant="link" className="mt-2 mb-10" size="sm" onClick={onClose}>
                <X size={38} strokeWidth={1} className="hover:text-[#111] text-[#555]" />
              </Button>
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full" orientation="vertical">
                <TabsList className="flex flex-col w-full h-auto bg-transparent">
                  <TabsTrigger 
                    value="general" 
                    className="flex items-center gap-2 justify-start w-full p-3 text-left hover:bg-gray-200 rounded-lg mb-1 data-[state=active]:bg-gray-200 data-[state=active]:shadow-sm"
                  >
                    <Settings size={21} />
                    <span>General</span>
                  </TabsTrigger>
                  <TabsTrigger 
                    value="account" 
                    className="flex items-center gap-2 justify-start w-full p-3 text-left hover:bg-gray-200 rounded-lg mb-1 data-[state=active]:bg-gray-200 data-[state=active]:shadow-sm"
                  >
                    <User size={21} />
                    <span>Account</span>
                  </TabsTrigger>
                  <TabsTrigger 
                    value="preferences" 
                    className="flex items-center gap-2 justify-start w-full p-3 text-left hover:bg-gray-200 rounded-lg mb-1 data-[state=active]:bg-gray-200 data-[state=active]:shadow-sm"
                  >
                    <Heart size={21} />
                    <span>Preferences</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col overflow-y-auto mx-4 lg:mx-8">
            {/* Mobile Header with Close Button and Navigation */}
            <div className="flex items-center justify-between py-4 lg:py-6 border-b">
              <div className="flex items-center gap-4">
                <Button variant="link" className="lg:hidden p-0" size="sm" onClick={onClose}>
                  <X size={24} strokeWidth={1} className="hover:text-[#111] text-[#555]" />
                </Button>
                <h2 className="text-lg lg:text-xl font-semibold capitalize">{activeTab}</h2>
              </div>
            </div>
            
            {/* Mobile Navigation Tabs */}
            <div className="lg:hidden border-b pt-1 pb-4">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3 bg-transparent">
                  <TabsTrigger 
                    value="general" 
                    className="flex items-center gap-2 justify-center p-3 data-[state=active]:bg-gray-200 data-[state=active]:shadow-sm"
                  >
                    <Settings size={18} />
                    <span className="text-sm">General</span>
                  </TabsTrigger>
                  <TabsTrigger 
                    value="account" 
                    className="flex items-center gap-2 justify-center p-3 data-[state=active]:bg-gray-200 data-[state=active]:shadow-sm"
                  >
                    <User size={18} />
                    <span className="text-sm">Account</span>
                  </TabsTrigger>
                  <TabsTrigger 
                    value="preferences" 
                    className="flex items-center gap-2 justify-center p-3 data-[state=active]:bg-gray-200 data-[state=active]:shadow-sm"
                  >
                    <Heart size={18} />
                    <span className="text-sm">Preferences</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
            <div className="py-2 flex-1 overflow-y-auto">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                {/* General Tab */}
                <TabsContent value="general" className="space-y-6">
                  <div className="space-y-4">
                    <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                      <Label htmlFor="language" className="text-sm font-medium">Language</Label>
                      <Select value={language} onValueChange={setLanguage}>
                        <SelectTrigger className="w-full sm:w-1/2 focus:ring-0">
                          <SelectValue placeholder="Select language" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="au">English(AU)</SelectItem>
                          <SelectItem value="en">English(US)</SelectItem>
                          <SelectItem value="es">Spanish</SelectItem>
                          <SelectItem value="fr">French</SelectItem>
                          <SelectItem value="de">German</SelectItem>
                          <SelectItem value="it">Italian</SelectItem>
                          <SelectItem value="pt">Portuguese</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                      <Label htmlFor="homeLocation" className="text-sm font-medium">Home Location</Label>
                      <Select value={homeLocation} onValueChange={setHomeLocation}>
                        <SelectTrigger className="w-full sm:w-1/2 focus:ring-0">
                          <SelectValue placeholder="Select your home location" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="queensland">Queensland, Australia</SelectItem>
                          <SelectItem value="sydney">Sydney, Australia</SelectItem>
                          <SelectItem value="melbourne">Melbourne, Australia</SelectItem>
                          <SelectItem value="brisbane">Brisbane, Australia</SelectItem>
                          <SelectItem value="perth">Perth, Australia</SelectItem>
                          <SelectItem value="auckland">Auckland, New Zealand</SelectItem>
                          <SelectItem value="wellington">Wellington, New Zealand</SelectItem>
                          <SelectItem value="queenstown">Queenstown, New Zealand</SelectItem>
                          <SelectItem value="gold-coast">Gold Coast, Australia</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                      <Label htmlFor="currency" className="text-sm font-medium">Currency</Label>
                      <Select value={currency} onValueChange={setCurrency}>
                        <SelectTrigger className="w-full sm:w-1/2 focus:ring-0">
                          <SelectValue placeholder="Select currency" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="aud">AUD - Australian Dollar</SelectItem>
                          <SelectItem value="nzd">NZD - New Zealand Dollar</SelectItem>
                          <SelectItem value="usd">USD - US Dollar</SelectItem>
                          <SelectItem value="eur">EUR - Euro</SelectItem>
                          <SelectItem value="gbp">GBP - British Pound</SelectItem>
                          <SelectItem value="cad">CAD - Canadian Dollar</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </TabsContent>

                {/* Account Tab */}
                <TabsContent value="account" className="space-y-6">
                  <div className="space-y-4">
                    <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                      <Label htmlFor="firstName" className="text-sm font-medium">First Name</Label>
                      <Input
                        id="firstName"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="Enter your first name"
                        className="w-full sm:w-2/3 focus:ring-0"
                      />
                    </div>

                    <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                      <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={email}
                        readOnly
                        placeholder="Email (read-only)"
                        className="w-full sm:w-2/3 focus:ring-0 bg-gray-50 cursor-not-allowed"
                      />
                    </div>

                    <div className="space-y-4 pt-4 border-b border-gray-100 pb-5">
                      <h3 className="font-medium border-gray-200 border-b pb-3">Change Password</h3>
                      <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                        <Label htmlFor="currentPassword" className="text-sm font-medium">Current Password</Label>
                        <Input
                          id="currentPassword"
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          placeholder="Enter current password"
                          className="w-full sm:w-2/3 focus:ring-0"
                          disabled={isChangingPassword}
                        />
                      </div>
                      <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 border-b border-gray-100 pb-5">
                        <Label htmlFor="newPassword" className="text-sm font-medium">New Password</Label>
                        <Input
                          id="newPassword"
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder="Enter new password"
                          className="w-full sm:w-2/3 focus:ring-0"
                          disabled={isChangingPassword}
                        />
                      </div>
                      <div className="space-y-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
                        <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm New Password</Label>
                        <Input
                          id="confirmPassword"
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Confirm new password"
                          className="w-full sm:w-2/3 focus:ring-0"
                          disabled={isChangingPassword}
                        />
                      </div>
                      <div className="flex justify-end">
                        <Button 
                          onClick={handlePasswordChange} 
                          disabled={isChangingPassword || !currentPassword || !newPassword || !confirmPassword}
                          variant="outline"
                        >
                          {isChangingPassword ? "Changing..." : "Change Password"}
                        </Button>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                {/* Preferences Tab */}
                <TabsContent value="preferences" className="space-y-6">
                  <div className="">
                    {/* Default Travellers Group */}
                    <div className="space-y-4">
                      <h3 className="font-medium">Default Travellers</h3>
                      <div className="grid grid-cols-3 gap-0 border-b border-gray-200">
                        <div className="flex gap-2 items-center pb-4">
                          <Input
                            id="adults"
                            type="number"
                            min="1"
                            max="10"
                            value={adults}
                            onChange={(e) => setAdults(e.target.value)}
                            className="w-[64px]"
                          />
                          <Label htmlFor="adults" className="italic">Adults</Label>
                        </div>
                        <div className="flex gap-2 items-center pb-4">
                          <Input
                            id="children"
                            type="number"
                            min="0"
                            max="10"
                            value={children}
                            onChange={(e) => setChildren(e.target.value)}
                            className="w-[64px]"
                          />
                          <Label htmlFor="children" className="italic">Children</Label>
                        </div>
                        <div className="flex gap-2 items-center pb-4">
                          <Input
                            id="childrenAgeList"
                            type="text"
                            value={childrenAgeList}
                            onChange={(e) => setChildrenAgeList(e.target.value.split(",").map(age => age.trim()))}
                            placeholder="8, 12"
                            className="w-[64px]"
                          />
                          <Label htmlFor="childrenAgeList" className="italic text-center">{"Children's Age"}</Label>
                        </div>
                      </div>
                    </div>

                    {/* Default Trip Type */}
                    <div className="mt-1 border-b border-gray-200 pt-2 pb-4">
                      <h3 className="font-medium mb-3">Default Trip Type</h3>
                      <RadioGroup value={tripType} onValueChange={setTripType}>
                        <div className="flex flex-wrap gap-6">
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="holiday" id="holiday" />
                            <Label htmlFor="holiday">Holiday</Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="work" id="work" />
                            <Label htmlFor="work">Work</Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="event" id="event" />
                            <Label htmlFor="event">Event/Special Occasion</Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="family" id="family" />
                            <Label htmlFor="family">Visit Family/Friends</Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="other" id="other" />
                            <Label htmlFor="other">Other:</Label>
                            <Input
                              id="otherTripType"
                              type="string"
                              value={otherTripType}
                              onChange={(e) => setOtherTripType(e.target.value)}
                              placeholder="Please specify..."
                              className="w-[200px] focus:ring-0"
                              disabled={tripType !== "other"}
                            />
                          </div>
                        </div>
                      </RadioGroup>
                    </div>

                    <div className="flex items-center justify-start gap-4 border-b border-gray-200">
                      {/* Default Budget */}
                      <div className="w-1/2">
                        <h3 className="font-medium pt-4 pb-4">Max Budget ($ / Night)</h3>
                        <div className="flex items-center justify-start gap-4 pb-4">
                          <Input
                            id="budget"
                            type="number"
                            value={budget}
                            onChange={(e) => setBudget(e.target.value)}
                            placeholder="Budget"
                            className="w-[90px] focus:ring-0"
                          />
                          <RadioGroup value={budgetType} onValueChange={setBudgetType}>
                            <div className="space-y-1">
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="flexible" id="flexible" />
                                <Label htmlFor="flexible">Flexible</Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="fixed" id="fixed" />
                                <Label htmlFor="fixed">Fixed Limit</Label>
                              </div>
                            </div>
                          </RadioGroup>
                        </div>
                      </div>
                      {/* Default Min Star Rating */}
                      <div className="w-1/2 border-l border-gray-200 pl-6 pb-4">
                        <h3 className="font-medium pt-4 pb-4">Default Min Star Rating</h3>
                        <Input
                          id="minStarRating"
                          type="number"
                          min="1"
                          max="5"
                          step="0.5"
                          value={minStarRating}
                          onChange={(e) => setMinStarRating(e.target.value)}
                          placeholder="Enter minimum star rating"
                          className="w-[64px] focus:ring-0"
                        />
                      </div>
                    </div>

                    {/* Search Preferences */}
                    <div className="space-y-3 pt-5">
                      <h3 className="font-medium ">Search Preferences</h3>
                      
                      {/* Selected Preferences */}
                      {selectedPreferences.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-3">
                          {selectedPreferences.map((pref) => {
                            const option = searchPreferencesOptions.find(opt => opt.value === pref);
                            return (
                              <div
                                key={pref}
                                className="flex items-center gap-1 bg-[#252d63] text-white px-3 py-1 rounded-full text-sm"
                              >
                                <span>{option?.label}</span>
                                <button
                                  type="button"
                                  onClick={() => handleRemovePreference(pref)}
                                  className="text-white hover:text-white/80 ml-1 rounded-full border border-white w-4 h-4 flex items-center justify-center"
                                >
                                  <X size={12} />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Search Input */}
                      <div className="relative">
                        <Input
                          value={searchInput}
                          onChange={(e) => setSearchInput(e.target.value)}
                          placeholder="Type to search preferences..."
                          className="focus:ring-0"
                        />
                        
                        {/* Dropdown Options */}
                        {searchInput && filteredOptions.length > 0 && (
                          <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-40 overflow-y-auto">
                            {filteredOptions.map((option) => (
                              <button
                                key={option.value}
                                type="button"
                                onClick={() => handleAddPreference(option.value)}
                                className="w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                              >
                                {option.label}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Available Options */}
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Available options:</h4>
                        <div className="grid grid-cols-3 gap-2">
                          {searchPreferencesOptions.map((option) => (
                            <div key={option.value} className="text-sm text-gray-600">
                              • {option.label}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 mt-3">
                        <span className="text-black font-medium">Note</span>: For better recommendation, it's better to choose important 2-3 preferences for you or your family.
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
            {/* Footer */}
            <div className="flex flex-col gap-3 p-4 lg:p-6 border-t">
              {saveMessage && (
                <div className={`text-sm ${saveMessage.includes("successfully") ? "text-green-600" : "text-red-600"}`}>
                  {saveMessage}
                </div>
              )}
              <div className="flex flex-col sm:flex-row justify-end gap-3">
                <Button variant="outline" onClick={onClose} disabled={isSaving} className="w-full sm:w-auto">
                  Cancel
                </Button>
                <Button onClick={handleSaveChanges} disabled={isSaving} className="w-full sm:w-auto">
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </div>
        </div>

        
      </div>
    </div>
  );
}
