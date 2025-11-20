"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/apiClient";

interface Collaborator {
  id: number;
  user_email: string;
  user_id?: number;
  role: "owner" | "editor" | "viewer";
  status: "pending" | "accepted" | "declined";
  invited_at: string;
  joined_at?: string;
}

interface GroupItineraryProps {
  itineraryId: number;
  onUpdate?: () => void;
}

export default function GroupItinerary({ itineraryId, onUpdate }: GroupItineraryProps) {
  const { user } = useAuth();
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"editor" | "viewer">("editor");

  useEffect(() => {
    loadCollaborators();
  }, [itineraryId]);

  const loadCollaborators = async () => {
    try {
      const data = await apiClient.get(`/api/itineraries/${itineraryId}/collaborators`);
      if (data.success) {
        setCollaborators(data.collaborators || []);
      }
    } catch (error) {
      console.error("Failed to load collaborators:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      alert("Please enter an email address");
      return;
    }

    try {
      const data = await apiClient.post(`/api/itineraries/${itineraryId}/collaborators`, {
        user_email: inviteEmail,
        role: inviteRole,
        invited_by_user_id: user?.id,
      });

      if (data.success) {
        alert("Invitation sent successfully!");
        setInviteEmail("");
        setShowInviteModal(false);
        loadCollaborators();
        onUpdate?.();
      } else {
        alert(data.error || "Failed to send invitation");
      }
    } catch (error: any) {
      alert(error.message || "Failed to send invitation");
    }
  };


  const handleRemoveCollaborator = async (collaboratorId: number) => {
    if (!confirm("Are you sure you want to remove this collaborator?")) return;

    try {
      const data = await apiClient.delete(
        `/api/itineraries/${itineraryId}/collaborators/${collaboratorId}`
      );
      if (data.success) {
        loadCollaborators();
        onUpdate?.();
      }
    } catch (error) {
      alert("Failed to remove collaborator");
    }
  };

  const handleAcceptInvite = async (collaboratorId: number) => {
    try {
      const data = await apiClient.put(
        `/api/itineraries/${itineraryId}/collaborators/${collaboratorId}`,
        { status: "accepted" }
      );
      if (data.success) {
        loadCollaborators();
        onUpdate?.();
      }
    } catch (error) {
      alert("Failed to accept invitation");
    }
  };


  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "owner":
        return "bg-purple-600";
      case "editor":
        return "bg-blue-600";
      case "viewer":
        return "bg-gray-600";
      default:
        return "bg-gray-600";
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case "accepted":
        return "bg-green-600";
      case "pending":
        return "bg-yellow-600";
      case "declined":
        return "bg-red-600";
      default:
        return "bg-gray-600";
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2">Loading collaborators...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-white">👥 Group Planning</h3>
        <button
          onClick={() => setShowInviteModal(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-semibold"
        >
          + Invite Collaborator
        </button>
      </div>

      {/* Collaborators List */}
      <div className="space-y-3">
        {collaborators.length === 0 ? (
          <p className="text-gray-400 text-center py-4">
            No collaborators yet. Invite friends to plan together!
          </p>
        ) : (
          collaborators.map((collab) => (
            <div
              key={collab.id}
              className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">
                    {collab.user_email.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-white font-medium">{collab.user_email}</p>
                  <div className="flex gap-2 mt-1">
                    <span
                      className={`px-2 py-0.5 rounded text-xs text-white ${getRoleBadgeColor(
                        collab.role
                      )}`}
                    >
                      {collab.role}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs text-white ${getStatusBadgeColor(
                        collab.status
                      )}`}
                    >
                      {collab.status}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {collab.status === "pending" && collab.user_email === user?.email && (
                  <button
                    onClick={() => handleAcceptInvite(collab.id)}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm"
                  >
                    Accept
                  </button>
                )}
                {(user?.id === collab.invited_by || collab.role === "owner") && (
                  <button
                    onClick={() => handleRemoveCollaborator(collab.id)}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-white text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-md border border-gray-700">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-white">Invite Collaborator</h3>
                <button
                  onClick={() => setShowInviteModal(false)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="friend@example.com"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as "editor" | "viewer")}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                  >
                    <option value="editor">Editor (can add/edit items)</option>
                    <option value="viewer">Viewer (read-only)</option>
                  </select>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleInvite}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-semibold"
                  >
                    Send Invitation
                  </button>
                  <button
                    onClick={() => setShowInviteModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

