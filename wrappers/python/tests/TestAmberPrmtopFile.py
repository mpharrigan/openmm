import unittest
from validateConstraints import *
from simtk.openmm.app import *
from simtk.openmm import *
from simtk.unit import *
import simtk.openmm.app.element as elem

prmtop1 = AmberPrmtopFile('systems/alanine-dipeptide-explicit.prmtop')
prmtop2 = AmberPrmtopFile('systems/alanine-dipeptide-implicit.prmtop')
prmtop3 = AmberPrmtopFile('systems/ff14ipq.parm7')
prmtop4 = AmberPrmtopFile('systems/Mg_water.prmtop')
inpcrd3 = AmberInpcrdFile('systems/ff14ipq.rst7')
inpcrd4 = AmberInpcrdFile('systems/Mg_water.inpcrd')

class TestAmberPrmtopFile(unittest.TestCase):

    """Test the AmberPrmtopFile.createSystem() method."""

    def test_NonbondedMethod(self):
        """Test all five options for the nonbondedMethod parameter."""

        methodMap = {NoCutoff:NonbondedForce.NoCutoff, 
                     CutoffNonPeriodic:NonbondedForce.CutoffNonPeriodic, 
                     CutoffPeriodic:NonbondedForce.CutoffPeriodic, 
                     Ewald:NonbondedForce.Ewald, PME: NonbondedForce.PME}
        for method in methodMap:
            system = prmtop1.createSystem(nonbondedMethod=method)
            forces = system.getForces()
            self.assertTrue(any(isinstance(f, NonbondedForce) and 
                                f.getNonbondedMethod()==methodMap[method] 
                                for f in forces))

    def test_Cutoff(self):
        """Test to make sure the nonbondedCutoff parameter is passed correctly."""

        for method in [CutoffNonPeriodic, CutoffPeriodic, Ewald, PME]:
            system = prmtop1.createSystem(nonbondedMethod=method, 
                                          nonbondedCutoff=2*nanometer, 
                                          constraints=HBonds)
            cutoff_distance = 0.0*nanometer
            cutoff_check = 2.0*nanometer
            for force in system.getForces():
                if isinstance(force, NonbondedForce):
                    cutoff_distance = force.getCutoffDistance()
            self.assertEqual(cutoff_distance, cutoff_check)

    def test_EwaldErrorTolerance(self):
        """Test to make sure the ewaldErrorTolerance parameter is passed correctly."""

        for method in [Ewald, PME]:
            system = prmtop1.createSystem(nonbondedMethod=method, 
                                          ewaldErrorTolerance=1e-6, 
                                          constraints=HBonds)
            tolerance = 0
            tolerance_check = 1e-6
            for force in system.getForces():
                if isinstance(force, NonbondedForce):
                    tolerance = force.getEwaldErrorTolerance()
            self.assertEqual(tolerance, tolerance_check)

    def test_RemoveCMMotion(self):
        """Test both options (True and False) for the removeCMMotion parameter."""

        for b in [True, False]:
            system = prmtop1.createSystem(removeCMMotion=b)
            forces = system.getForces()
            self.assertEqual(any(isinstance(f, CMMotionRemover) for f in forces), b)

    def test_RigidWaterAndConstraints(self):
        """Test all eight options for the constraints and rigidWater parameters."""

        topology = prmtop1.topology
        for constraints_value in [None, HBonds, AllBonds, HAngles]:
            for rigidWater_value in [True, False]:
                system = prmtop1.createSystem(constraints=constraints_value, 
                                              rigidWater=rigidWater_value)
                validateConstraints(self, topology, system, 
                                    constraints_value, rigidWater_value)

    def test_ImplicitSolvent(self):
        """Test the four types of implicit solvents using the implicitSolvent 
        parameter.

        """
        for implicitSolvent_value in [HCT, OBC1, OBC2, GBn]:
            system = prmtop2.createSystem(implicitSolvent=implicitSolvent_value)
            forces = system.getForces()
            if implicitSolvent_value in set([HCT, OBC1, GBn]):
                force_type = CustomGBForce
            else:
                force_type = GBSAOBCForce
            
            self.assertTrue(any(isinstance(f, force_type) for f in forces))

    def test_ImplicitSolventParameters(self):
        """Test that parameters are set correctly for the different types of implicit solvent."""
        methodMap = {NoCutoff:NonbondedForce.NoCutoff,
                     CutoffNonPeriodic:NonbondedForce.CutoffNonPeriodic}
        for implicitSolvent_value in [HCT, OBC1, OBC2, GBn]:
            for method in methodMap:
                system = prmtop2.createSystem(implicitSolvent=implicitSolvent_value, 
                                    solventDielectric=50.0, soluteDielectric=0.9, nonbondedMethod=method)
                found_matching_solvent_dielectric=False
                found_matching_solute_dielectric=False
                if implicitSolvent_value in set([HCT, OBC1, GBn]):
                    for force in system.getForces():
                        if isinstance(force, CustomGBForce):
                            self.assertEqual(force.getNonbondedMethod(), methodMap[method])
                            for j in range(force.getNumGlobalParameters()):
                                if (force.getGlobalParameterName(j) == 'solventDielectric' and
                                   force.getGlobalParameterDefaultValue(j) == 50.0):
                                    found_matching_solvent_dielectric = True
                                if (force.getGlobalParameterName(j) == 'soluteDielectric' and
                                   force.getGlobalParameterDefaultValue(j) == 0.9):
                                    found_matching_solute_dielectric = True
                        if isinstance(force, NonbondedForce):
                            self.assertEqual(force.getReactionFieldDielectric(), 1.0)
                            self.assertEqual(force.getNonbondedMethod(), methodMap[method])
                    self.assertTrue(found_matching_solvent_dielectric and 
                                    found_matching_solute_dielectric)
                else:
                    for force in system.getForces():
                        if isinstance(force, GBSAOBCForce):
                            self.assertEqual(force.getNonbondedMethod(), methodMap[method])
                            if force.getSolventDielectric() == 50.0:
                                found_matching_solvent_dielectric = True
                            if force.getSoluteDielectric() == 0.9:
                                found_matching_solute_dielectric = True
                        if isinstance(force, NonbondedForce):
                            self.assertEqual(force.getReactionFieldDielectric(), 1.0)
                            self.assertEqual(force.getNonbondedMethod(), methodMap[method])
                    self.assertTrue(found_matching_solvent_dielectric and 
                                    found_matching_solute_dielectric)

    def test_HydrogenMass(self):
        """Test that altering the mass of hydrogens works correctly."""
        
        topology = prmtop1.topology
        hydrogenMass = 4*amu
        system1 = prmtop1.createSystem()
        system2 = prmtop1.createSystem(hydrogenMass=hydrogenMass)
        for atom in topology.atoms():
            if atom.element == elem.hydrogen:
                self.assertNotEqual(hydrogenMass, system1.getParticleMass(atom.index))
                self.assertEqual(hydrogenMass, system2.getParticleMass(atom.index))
        totalMass1 = sum([system1.getParticleMass(i) for i in range(system1.getNumParticles())]).value_in_unit(amu)
        totalMass2 = sum([system2.getParticleMass(i) for i in range(system2.getNumParticles())]).value_in_unit(amu)
        self.assertAlmostEqual(totalMass1, totalMass2)

    def test_NBFIX_LongRange(self):
        """Test prmtop files with NBFIX LJ modifications w/ long-range correction"""
        system = prmtop3.createSystem(nonbondedMethod=PME,
                                      nonbondedCutoff=8*angstroms)
        # Check the forces
        has_nonbond_force = has_custom_nonbond_force = False
        nonbond_exceptions = custom_nonbond_exclusions = 0
        for force in system.getForces():
            if isinstance(force, NonbondedForce):
                has_nonbond_force = True
                nonbond_exceptions = force.getNumExceptions()
            elif isinstance(force, CustomNonbondedForce):
                has_custom_nonbond_force = True
                custom_nonbond_exceptions = force.getNumExclusions()
        self.assertTrue(has_nonbond_force)
        self.assertTrue(has_custom_nonbond_force)
        self.assertEqual(nonbond_exceptions, custom_nonbond_exceptions)
        integrator = VerletIntegrator(1.0*femtoseconds)
        # Use reference platform, since it should always be present and
        # 'working', and the system is plenty small so this won't be too slow
        sim = Simulation(prmtop3.topology, system, integrator, Platform.getPlatformByName('Reference'))
        # Check that the energy is about what we expect it to be
        sim.context.setPeriodicBoxVectors(*inpcrd3.boxVectors)
        sim.context.setPositions(inpcrd3.positions)
        ene = sim.context.getState(getEnergy=True, enforcePeriodicBox=True).getPotentialEnergy()
        ene = ene.value_in_unit(kilocalories_per_mole)
        # Make sure the energy is relatively close to the value we get with
        # Amber using this force field.
        self.assertAlmostEqual(-7099.44989739/ene, 1, places=3)

    def test_NBFIX_noLongRange(self):
        """Test prmtop files with NBFIX LJ modifications w/out long-range correction"""
        system = prmtop3.createSystem(nonbondedMethod=PME,
                                      nonbondedCutoff=8*angstroms)
        # Check the forces
        has_nonbond_force = has_custom_nonbond_force = False
        nonbond_exceptions = custom_nonbond_exclusions = 0
        for force in system.getForces():
            if isinstance(force, NonbondedForce):
                has_nonbond_force = True
                nonbond_exceptions = force.getNumExceptions()
            elif isinstance(force, CustomNonbondedForce):
                has_custom_nonbond_force = True
                custom_nonbond_exceptions = force.getNumExclusions()
                force.setUseLongRangeCorrection(False)
        self.assertTrue(has_nonbond_force)
        self.assertTrue(has_custom_nonbond_force)
        self.assertEqual(nonbond_exceptions, custom_nonbond_exceptions)
        integrator = VerletIntegrator(1.0*femtoseconds)
        # Use reference platform, since it should always be present and
        # 'working', and the system is plenty small so this won't be too slow
        sim = Simulation(prmtop3.topology, system, integrator, Platform.getPlatformByName('Reference'))
        # Check that the energy is about what we expect it to be
        sim.context.setPeriodicBoxVectors(*inpcrd3.getBoxVectors())
        sim.context.setPositions(inpcrd3.getPositions())
        ene = sim.context.getState(getEnergy=True, enforcePeriodicBox=True).getPotentialEnergy()
        ene = ene.value_in_unit(kilocalories_per_mole)
        # Make sure the energy is relatively close to the value we get with
        # Amber using this force field.
        self.assertAlmostEqual(-7042.3903307/ene, 1, places=3)

    def test_LJ1264(self):
        """Test prmtop with 12-6-4 vdW potential implemented"""
        system = prmtop4.createSystem(nonbondedMethod=PME,
                                      nonbondedCutoff=8*angstroms)
        # Check the forces
        has_nonbond_force = has_custom_nonbond_force = False
        nonbond_exceptions = custom_nonbond_exclusions = 0
        for force in system.getForces():
            if isinstance(force, NonbondedForce):
                has_nonbond_force = True
                nonbond_exceptions = force.getNumExceptions()
                force.setUseDispersionCorrection(False)
            elif isinstance(force, CustomNonbondedForce):
                self.assertTrue(force.getUseLongRangeCorrection())
                has_custom_nonbond_force = True
                custom_nonbond_exceptions = force.getNumExclusions()
                force.setUseLongRangeCorrection(False)
        self.assertTrue(has_nonbond_force)
        self.assertTrue(has_custom_nonbond_force)
        self.assertEqual(nonbond_exceptions, custom_nonbond_exceptions)
        integrator = VerletIntegrator(1.0*femtoseconds)
        # Use reference platform, since it should always be present and
        # 'working', and the system is plenty small so this won't be too slow
        sim = Simulation(prmtop4.topology, system, integrator, Platform.getPlatformByName('Reference'))
        # Check that the energy is about what we expect it to be
        sim.context.setPeriodicBoxVectors(*inpcrd4.boxVectors)
        sim.context.setPositions(inpcrd4.positions)
        ene = sim.context.getState(getEnergy=True, enforcePeriodicBox=True).getPotentialEnergy()
        ene = ene.value_in_unit(kilocalories_per_mole)
        # Make sure the energy is relatively close to the value we get with
        # Amber using this force field.
        self.assertAlmostEqual(-7307.2735621/ene, 1, places=3)

if __name__ == '__main__':
    unittest.main()
