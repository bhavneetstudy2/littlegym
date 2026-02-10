'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type { Curriculum, Skill, Child, SkillProgress } from '@/types';

export default function ProgressPage() {
  const { selectedCenter } = useCenter();
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [selectedCurriculum, setSelectedCurriculum] = useState<number | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [children, setChildren] = useState<Child[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [childProgress, setChildProgress] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchCurricula();
    fetchChildren();
  }, [selectedCenter]);

  useEffect(() => {
    if (selectedCurriculum) {
      fetchSkills(selectedCurriculum);
    }
  }, [selectedCurriculum]);

  useEffect(() => {
    if (selectedChild) {
      fetchChildProgress(selectedChild);
    }
  }, [selectedChild, selectedCurriculum]);

  const fetchCurricula = async () => {
    try {
      const data = await api.get<Curriculum[]>('/api/v1/curriculum');
      setCurricula(data);
      if (data.length > 0) {
        setSelectedCurriculum(data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch curricula:', err);
    }
  };

  const fetchSkills = async (curriculumId: number) => {
    try {
      const data = await api.get<Skill[]>(`/api/v1/curriculum/${curriculumId}/skills`);
      setSkills(data);
    } catch (err) {
      console.error('Failed to fetch skills:', err);
    }
  };

  const fetchChildren = async () => {
    try {
      // Get children from enrollments
      const centerParam = selectedCenter ? `&center_id=${selectedCenter.id}` : '';
      const enrollments = await api.get<any[]>(`/api/v1/enrollments?status=ACTIVE${centerParam}`);
      const uniqueChildren = Array.from(
        new Map(enrollments.map((e) => [e.child.id, e.child])).values()
      ) as Child[];
      setChildren(uniqueChildren);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch children:', err);
      setLoading(false);
    }
  };

  const fetchChildProgress = async (childId: number) => {
    try {
      const data = await api.get<any[]>(
        `/api/v1/curriculum/progress/children/${childId}${
          selectedCurriculum ? `?curriculum_id=${selectedCurriculum}` : ''
        }`
      );
      setChildProgress(data);
    } catch (err) {
      console.error('Failed to fetch child progress:', err);
    }
  };

  const updateSkillProgress = async (skillId: number, level: string) => {
    if (!selectedChild) return;

    setUpdating(true);
    try {
      await api.post('/api/v1/curriculum/progress', {
        child_id: selectedChild,
        skill_id: skillId,
        level: level,
      });
      await fetchChildProgress(selectedChild);
    } catch (err) {
      console.error('Failed to update skill progress:', err);
      alert('Failed to update progress');
    } finally {
      setUpdating(false);
    }
  };

  const getProgressLevel = (skillId: number): string => {
    const progress = childProgress.find((p) => p.skill_id === skillId);
    return progress ? progress.level : 'NOT_STARTED';
  };

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      NOT_STARTED: 'bg-gray-100 text-gray-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      ACHIEVED: 'bg-green-100 text-green-800',
      MASTERED: 'bg-purple-100 text-purple-800',
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  const getLevelLabel = (level: string) => {
    const labels: Record<string, string> = {
      NOT_STARTED: 'Not Started',
      IN_PROGRESS: 'In Progress',
      ACHIEVED: 'Achieved',
      MASTERED: 'Mastered',
    };
    return labels[level] || level;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Skill Progress Tracking</h1>
        <p className="text-gray-600">Track student progress across curriculum skills</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Child
            </label>
            <select
              value={selectedChild || ''}
              onChange={(e) => setSelectedChild(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select a child --</option>
              {children.map((child) => (
                <option key={child.id} value={child.id}>
                  {child.first_name} {child.last_name || ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Curriculum
            </label>
            <select
              value={selectedCurriculum || ''}
              onChange={(e) => setSelectedCurriculum(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select curriculum --</option>
              {curricula.map((curriculum) => (
                <option key={curriculum.id} value={curriculum.id}>
                  {curriculum.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Skills Progress */}
      {selectedChild && selectedCurriculum ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Skills Checklist - {children.find((c) => c.id === selectedChild)?.first_name}
            </h2>
          </div>

          {skills.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No skills found for this curriculum
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {skills.map((skill) => {
                const currentLevel = getProgressLevel(skill.id);
                return (
                  <div key={skill.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{skill.name}</h3>
                        {skill.description && (
                          <p className="text-sm text-gray-500 mt-1">{skill.description}</p>
                        )}
                        {skill.category && (
                          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded mt-2">
                            {skill.category}
                          </span>
                        )}
                      </div>

                      <div className="ml-4 flex gap-2">
                        {['NOT_STARTED', 'IN_PROGRESS', 'ACHIEVED', 'MASTERED'].map((level) => (
                          <button
                            key={level}
                            onClick={() => updateSkillProgress(skill.id, level)}
                            disabled={updating}
                            className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                              currentLevel === level
                                ? getLevelColor(level)
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            } ${updating ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            {getLevelLabel(level)}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Please select a child and curriculum to view and update progress
        </div>
      )}
    </div>
  );
}
